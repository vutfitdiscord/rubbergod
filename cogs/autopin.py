import datetime
import discord
from discord.ext import commands

from config.app_config import Config
from config.messages import Messages


class AutoPin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """
        if the message has X or more 'pin' emojis pin the message
        """
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.errors.NotFound:
            return
        emoji = payload.emoji.name
        if emoji == "📌":
            for reaction in message.reactions:
                if (
                    reaction.emoji == "📌"
                    and reaction.count >= Config.autopin_count
                    and not message.pinned
                    and message.type == discord.MessageType.default
                    and message.channel.id not in Config.autopin_banned_channels
                ):
                    pin_count = await channel.pins()
                    if len(pin_count) == 50:
                        await channel.send(Messages.autopin_max_pins_error)
                        return
                    users = await reaction.users().flatten()
                    await self.log(message, users)
                    await message.pin()
                    await message.clear_reaction("📌")
                    break

    async def log(self, message, users):
        """
        Logging message link and users that pinned message
        """
        embed = discord.Embed(title="📌 Auto pin message log", color=0xEEE657)
        user_names = ", ".join([user.name for user in users])
        message_link = message.jump_url
        embed.add_field(name="Users", value=user_names)
        embed.add_field(name="In channel", value=message.channel)
        embed.add_field(name="Message", value=message_link, inline=False)
        embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        channel = self.bot.get_channel(Config.log_channel)
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(AutoPin(bot))
