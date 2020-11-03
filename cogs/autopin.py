import datetime
import discord
from discord.ext import commands

from config.app_config import Config
from config.messages import Messages


class AutoPin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def hadle_reaction(self, ctx):
        """
        if the message has X or more 'pin' emojis pin the message
        """
        reaction = ctx["emoji"]
        message = ctx["message"]
        channel = ctx["channel"]
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
        embed.add_field(name="Users", value=user_names if len(user_names) > 0 else "**Missing users**")
        embed.add_field(name="In channel", value=message.channel)
        embed.add_field(name="Message", value=message_link, inline=False)
        embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        channel = self.bot.get_channel(Config.log_channel)
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(AutoPin(bot))
