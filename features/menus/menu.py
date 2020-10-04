import asyncio
from typing import Union

import discord
from discord import Message, User, Member
from discord.ext.commands import Bot, Context
from discord.ext.menus import button, Last, MenuPages, First

from config.app_config import Config

config = Config()

MemberLike = Union[User, Member]


class CustomPagedMenu(MenuPages):
    """
    Handles some very much unexpected things with discord.ext.menu's.

        - Setting an emoji on button that discord does not recognise would
          make pagination silently fail. This class hacks it so these
          exceptions are raised in start() call and thus propagated
          into command caller.
    """

    async def start(self, ctx, *, channel=None, wait=False):
        """
        Starts the pagination by sending the first page and then
        blocks until the pagination session finishes.

        :raises Exception: Propagates errors from inner tasks.
        """
        await super().start(ctx, channel=channel, wait=wait)
        _inner_exceptions = list()

        def task_exc_cleaner(fut: asyncio.Future):
            exc = fut.exception()
            if exc:
                _inner_exceptions.append(exc)

        for task in self._Menu__tasks:  # noqa
            task.add_done_callback(task_exc_cleaner)

        while True:
            # need to check at the end
            # the menu's main loop might be already finished but we
            # need to check errors at least once more because that
            # will be the moment when all task's done_callbacks should be finished too
            for exc in _inner_exceptions:
                raise Exception("Inner task raised exception.") from exc

            if self._event.is_set():
                return
            await asyncio.sleep(0.05)


class AuthorOnlyPagedMenu(CustomPagedMenu, inherit_buttons=False):
    """
    MenuPage that allows react control only for the message owner or admins.
    """

    bot: Bot
    ctx: Context
    message: Message
    author: MemberLike = None

    def __init__(self, source, **kwargs):
        super().__init__(source, **kwargs)

    async def start(self, ctx: Context, *, channel=None, wait=False):
        self.author = ctx.author
        await super().start(ctx, channel=channel, wait=wait)

    @staticmethod
    def _is_add_event(payload: discord.RawReactionActionEvent) -> bool:
        return payload.event_type == "REACTION_ADD"

    def _is_author_or_admin(self, payload: discord.RawReactionActionEvent) -> bool:
        return payload.user_id == self.author.id or payload.user_id in config.admin_ids

    async def _try_remove_reaction(self, payload: discord.RawReactionActionEvent):
        if self.ctx.message.guild and self.ctx.message.guild.me.guild_permissions.manage_messages:
            # try removing the reaction afterwards
            try:
                await self.message.remove_reaction(payload.emoji, payload.member)
            except discord.DiscordException:
                pass

    async def _main_checks(self, payload: discord.RawReactionActionEvent) -> bool:
        if self._is_add_event(payload):
            asyncio.ensure_future(self._try_remove_reaction(payload), loop=self.bot.loop)
            if self._is_author_or_admin(payload):
                return True
        return False

    def _skip_fast_forward_first(self):
        return self.current_page <= 1

    @button('\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f',
            position=First(0), skip_if=_skip_fast_forward_first)
    async def go_to_first_page(self, payload):
        """go to the first page"""
        if await self._main_checks(payload):
            await self.show_page(0)

    @button('\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f', position=First(1))
    async def go_to_previous_page(self, payload):
        """go to the previous page"""
        if await self._main_checks(payload):
            await self.show_checked_page(self.current_page - 1)

    @button('\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f', position=Last(0))
    async def go_to_next_page(self, payload):
        """go to the next page"""
        if await self._main_checks(payload):
            await self.show_checked_page(self.current_page + 1)

    def _skip_fast_forward_last(self):
        return self._source.get_max_pages() <= 2

    @button('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f',
            position=Last(1), skip_if=_skip_fast_forward_last)
    async def go_to_last_page(self, payload):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        if await self._main_checks(payload):
            await self.show_page(self._source.get_max_pages() - 1)

    @button('\N{BLACK SQUARE FOR STOP}\ufe0f', position=Last(2))
    async def stop_pages(self, payload):
        """stops the pagination session."""
        if await self._main_checks(payload):
            self.stop()
