import re

import disnake

from buttons.base import BaseView
from utils.checks import PermissionsCheck

from .messages_cz import MessagesCZ

CLEAN_HISTORY_SECONDS = 3600  # purge messages from the last hour across the whole guild


def _extract_user_id(inter: disnake.MessageInteraction) -> int:
    """Extract the offending user's id from the alert embed's footer."""
    footer_text = inter.message.embeds[0].footer.text or ""
    match = re.match(r"User ID: (\d+)", footer_text)
    if match is None:
        raise ValueError(f"Could not extract user id from footer: {footer_text!r}")
    return int(match.group(1))


class ScamView(BaseView):
    """Persistent view posted alongside a scam alert in the mod room."""

    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    async def interaction_check(self, inter: disnake.MessageInteraction) -> bool:
        return PermissionsCheck.is_submod_plus(inter, raise_exception=False)

    @disnake.ui.button(
        label=MessagesCZ.scam_ban_unban_button,
        emoji="🔨",
        style=disnake.ButtonStyle.red,
        custom_id="scamguard:ban_unban",
    )
    async def ban_unban(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()
        user_id = _extract_user_id(inter)
        user = disnake.Object(id=user_id)

        try:
            await inter.guild.ban(
                user,
                clean_history_duration=CLEAN_HISTORY_SECONDS,
                reason="ScamGuard: MrBeast crypto scam spam",
            )
            await inter.guild.unban(user, reason="ScamGuard: unbanned right after purge")
            content = MessagesCZ.scam_ban_unban_done(
                author=inter.author.mention, user=f"<@{user_id}>", hours=CLEAN_HISTORY_SECONDS // 3600
            )
        except disnake.Forbidden:
            content = MessagesCZ.scam_ban_unban_forbidden(user=f"<@{user_id}>")
        except disnake.HTTPException as error:
            content = MessagesCZ.scam_ban_unban_failed(user=f"<@{user_id}>", error=error)

        button.disabled = True
        await inter.edit_original_response(view=self)
        await inter.channel.send(content, allowed_mentions=disnake.AllowedMentions.none())

        cog = self.bot.get_cog("ScamGuard")
        if cog is not None:
            cog.clear_alert(user_id)
