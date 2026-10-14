"""
Cog for detecting MrBeast-impersonation crypto scam spam.

Compromised/fake accounts periodically mass-post the same handful of casino
screenshots together with an @everyone/@here ping and no text content, usually
to several channels at once. This reuses warden's dhash image-comparison
approach (see cogs/warden/cog.py) to match attachments against a small set of
known scam screenshots, deletes every matching message automatically, and
posts a single, updating prompt per account in the mod room to ban -> unban it
(which purges its recent messages across the whole server).
"""

import asyncio
import time

import dhash
import disnake
from disnake.ext import commands

from cogs.base import Base
from rubbergod import Rubbergod

from . import features
from .messages_cz import MessagesCZ
from .views import ScamView

dhash.force_pil()

# Messages from the same account within this window are treated as one incident
# and collapse into a single, updated mod-room alert instead of spamming one per channel.
ALERT_MERGE_WINDOW_SECONDS = 600


class ScamGuard(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot
        self.reference_hashes = features.load_reference_hashes()
        # user_id -> {"message": disnake.Message, "channel_ids": dict[int, None], "expires": float}
        self.active_alerts: dict[int, dict] = {}
        self._alert_lock = asyncio.Lock()

    @commands.Cog.listener("on_ready")
    async def init_views(self):
        """Instantiate the persistent view so button clicks survive bot restarts"""
        self.bot.add_view(ScamView(self.bot))

    def doCheckScam(self, message: disnake.Message) -> bool:
        return (
            message.guild is not None
            and not message.author.bot
            and message.mention_everyone
            and len(message.attachments) > 0
        )

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if not self.doCheckScam(message):
            return

        attachment = await features.find_matching_attachment(message, self.reference_hashes)
        if attachment is not None:
            await self._handle_scam(message, attachment)

    def clear_alert(self, user_id: int) -> None:
        """Drop the merge window for a user, e.g. once a mod has acted on the alert."""
        self.active_alerts.pop(user_id, None)

    async def _handle_scam(self, message: disnake.Message, attachment: disnake.Attachment) -> None:
        author = message.author
        # grab evidence before deleting the message, the attachment CDN link won't survive that
        evidence = await attachment.to_file()

        try:
            await message.delete()
        except disnake.NotFound:
            pass

        async with self._alert_lock:
            now = time.monotonic()
            # opportunistically drop other expired entries so the dict doesn't grow forever
            for stale_id in [uid for uid, entry in self.active_alerts.items() if entry["expires"] < now]:
                del self.active_alerts[stale_id]

            entry = self.active_alerts.get(author.id)
            if entry is not None:
                entry["channel_ids"][message.channel.id] = None
                entry["expires"] = now + ALERT_MERGE_WINDOW_SECONDS
                await self._update_alert(author, entry)
                return

            channel_ids = {message.channel.id: None}
            embed = self._build_embed(author, channel_ids, evidence.filename)
            alert_message = await self.mod_room.send(embed=embed, file=evidence, view=ScamView(self.bot))
            self.active_alerts[author.id] = {
                "message": alert_message,
                "channel_ids": channel_ids,
                "filename": evidence.filename,
                "expires": now + ALERT_MERGE_WINDOW_SECONDS,
            }

    async def _update_alert(self, author: disnake.Member, entry: dict) -> None:
        embed = self._build_embed(author, entry["channel_ids"], entry["filename"])
        try:
            await entry["message"].edit(embed=embed)
        except disnake.NotFound:
            # alert message was deleted, start fresh next time
            self.active_alerts.pop(author.id, None)

    def _build_embed(
        self, author: disnake.Member, channel_ids: dict[int, None], filename: str
    ) -> disnake.Embed:
        channels = ", ".join(f"<#{channel_id}>" for channel_id in channel_ids)
        embed = disnake.Embed(
            title=MessagesCZ.scam_detected_title,
            description=MessagesCZ.scam_detected_description(
                user=author.mention, user_name=str(author), channel=channels
            ),
            color=disnake.Color.red(),
        )
        embed.add_field(name="Nápověda", value=MessagesCZ.scam_detected_hint, inline=False)
        embed.set_image(url=f"attachment://{filename}")
        embed.set_footer(text=f"User ID: {author.id}")
        return embed
