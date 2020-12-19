import datetime
import discord
import utils
from discord.ext import commands
from repository import pin_repo

from config.app_config import Config
from config.messages import Messages


class AutoPin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.repo = pin_repo.PinRepository()

    @commands.command()
    @commands.check(utils.helper_plus)
    async def repin(self, ctx, *args):
        try:
            converter = commands.MessageConverter()
            message: discord.Message = await converter.convert(ctx=ctx, argument=" ".join(args))

            if message.pinned:
                await message.unpin()
            await message.pin()
        except commands.errors.BadArgument:
            await ctx.send(Messages.autopin_repin_unknown_message)
            return

    @commands.check(utils.helper_plus)
    @commands.group(pass_context=True)
    async def pin(self, ctx: commands.Context):
        """
        Controls auto pin.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(Messages.autopin_help)

    @pin.command()
    async def add(self, ctx: commands.Context, message_url: str):
        try:
            converter = commands.MessageConverter()
            message: discord.Message = await converter.convert(ctx, message_url)

            self.repo.add_or_update_channel(str(message.channel.id), str(message.id))
            await ctx.send(Messages.autopin_add_done)
        except commands.errors.BadArgument:
            await ctx.send(Messages.autopin_add_unknown_message)
            return

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
