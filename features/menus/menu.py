import asyncio

import disnake
from disnake import Message
from disnake.ext.commands import Bot, Context
from disnake.ext.menus import button, Last, First

from config.app_config import config
from features.menus.base import BlockingPagedMenu, MemberLike


class AuthorOnlyPagedMenu(BlockingPagedMenu, inherit_buttons=False):
    """
    Menu that allows react control only for the message owner or admins.
    """
    bot: Bot
    ctx: Context
    message: Message
    author: MemberLike = None

    def __init__(self, source, **kwargs):
        super().__init__(source, **kwargs)

    async def start(self, ctx: Context, *, channel=None, wait=False):
        assert (hasattr(ctx, "author")
                and ctx.author), "ctx.author does not exists or is falsy, that's unexpected"

        self.author = ctx.author
        await super().start(ctx, channel=channel, wait=wait)

    @staticmethod
    def _is_add_event(payload: disnake.RawReactionActionEvent) -> bool:
        return hasattr(payload, "event_type") and payload.event_type == "REACTION_ADD"

    def _is_author_or_admin(self, payload: disnake.RawReactionActionEvent) -> bool:
        return hasattr(payload, "user_id") and (
                payload.user_id == self.author.id or payload.user_id in config.admin_ids
        )

    async def _try_remove_reaction(self, payload: disnake.RawReactionActionEvent):
        if self.ctx.message.guild and self.ctx.message.guild.me.guild_permissions.manage_messages:
            # try removing the reaction afterwards
            try:
                await self.message.remove_reaction(payload.emoji, payload.member)
            except (disnake.DiscordException, AttributeError):
                pass

    async def _checks(self, payload: disnake.RawReactionActionEvent, remove_react_after=True) -> bool:
        """Checks it's reaction ADD event and message ownership.
        Additionally allows for the users react removal.
        """
        if self._is_add_event(payload):
            if remove_react_after:
                asyncio.ensure_future(self._try_remove_reaction(payload), loop=self.bot.loop)
            if self._is_author_or_admin(payload):
                return True
        return False

    def _check_fast_forward(self):
        return self._source.get_max_pages() < 3

    @button("\N{BLACK LEFT-POINTING TRIANGLE}\ufe0f", position=First(1))
    async def go_to_previous_page(self, payload):
        """go to the previous page"""
        if await self._checks(payload):
            await self.show_checked_page(self.current_page - 1)

    @button("\N{BLACK RIGHT-POINTING TRIANGLE}\ufe0f", position=Last(0))
    async def go_to_next_page(self, payload):
        """go to the next page"""
        if await self._checks(payload):
            await self.show_checked_page(self.current_page + 1)

    @button(
        "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f",
        position=First(0),
        skip_if=_check_fast_forward,
    )
    async def go_to_first_page(self, payload):
        """go to the first page"""
        if await self._checks(payload):
            await self.show_page(0)

    @button(
        "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}\ufe0f",
        position=Last(1),
        skip_if=_check_fast_forward,
    )
    async def go_to_last_page(self, payload):
        """go to the last page"""
        # The call here is safe because it's guarded by skip_if
        if await self._checks(payload):
            await self.show_page(self._source.get_max_pages() - 1)

    @button("\N{BLACK SQUARE FOR STOP}\ufe0f", position=Last(2))
    async def stop_pages(self, payload):
        """stops the pagination session."""
        if await self._checks(payload):
            self.stop()
