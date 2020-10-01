from typing import Union

from discord import Message, User, Member
from discord.ext.commands import Bot, Context
from discord.ext.menus import MenuPages, button, Last
from discord.raw_models import RawReactionActionEvent

from config.app_config import Config

config = Config()

MemberLike = Union[User, Member]


class AuthorOnlyPagedMenu(MenuPages):
    """
    MenuPage that allows react control only for the message owner or admins.
    """

    bot: Bot
    ctx: Context
    message: Message
    author: MemberLike = None

    def __init__(self, *args, **kwargs):
        if kwargs.get("delete_message_after") and kwargs.get("clear_reactions_after"):
            # don't clear reactions if the message gets deleted
            kwargs["clear_reactions_after"] = False

        super().__init__(*args, **kwargs)

    def is_msg_author_or_admin(self, react_payload: RawReactionActionEvent) -> bool:
        return react_payload.user_id == self.author.id or react_payload.user_id in config.admin_ids

    @button("\N{BLACK SQUARE FOR STOP}\ufe0f", position=Last(2))
    async def stop_pages(self, payload: RawReactionActionEvent):
        """stops the pagination session (and deletes the message) if requested by owner of the message or admin"""
        if (
                payload.event_type != "REACTION_ADD"
                or (hasattr(payload, "bot") and payload.bot)
                or not hasattr(payload, "member")
        ):
            return

        if self.is_msg_author_or_admin(payload):
            self.stop()
        elif self.ctx.message.guild and self.ctx.message.guild.me.guild_permissions.manage_messages:
            # remove intruder's emoji
            await self.message.remove_reaction(payload.emoji, payload.member)

    async def start(self, ctx: Context, *, channel=None, wait=False):
        self.author = ctx.author
        return await super().start(ctx, channel=channel, wait=wait)
