from random import choice

import discord
from discord.ext import commands

import utils
from config import app_config
from repository.hugs_repo import HugsRepository
from .menus import get_hugboard_menu, get_top_huggers_menu, get_top_hugged_menu

config = app_config.Config


class Hugs(commands.Cog):
    """
    Hugging commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.hugs_repo = HugsRepository()

    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def hugboard(self, ctx: commands.Context):
        """
        Overall hugging stats.
        """
        async with ctx.typing():
            menu = get_hugboard_menu()

        await menu.start(ctx)

    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def huggers(self, ctx: commands.Context):
        """
        Get the biggest huggers.
        """
        async with ctx.typing():
            menu = get_top_huggers_menu()

        await menu.start(ctx)

    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def hugged(self, ctx: commands.Context):
        """
        Get the most hugged.
        """
        async with ctx.typing():
            menu = get_top_hugged_menu()

        await menu.start(ctx)

    @commands.cooldown(rate=5, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def hugs(self, ctx: commands.Context):
        """
        Get your lovely hug stats.
        """
        async with ctx.typing():
            stats = self.hugs_repo.get_members_stats(ctx.author.id)
            positions = self.hugs_repo.get_member_position(stats)
            avg_position = int((positions[0] + positions[1]) // 2)

            embed = discord.Embed(
                title="Your Lovely Hug Stats <:peepoHugger:761293739041620038>",
                description=" | ".join(
                    (
                        "**Ranks**",
                        f"Given: **{positions[0]}.**",
                        f"Received: **{positions[1]}.**",
                        f"Avg: **{avg_position}.**",
                    )
                ),
            )
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

            if ctx.guild and ctx.guild.id == config.guild_id:
                given_emoji = "<:peepohugs:761297281743716373>"
                recv_emoji = "<:huggers:602823825880514561>"
            else:
                given_emoji = recv_emoji = ":people_hugging:"

            embed.add_field(name=f"{given_emoji} Given", value=str(stats.given))
            embed.add_field(name=f"{recv_emoji} Received", value=str(stats.received))

        await ctx.send(embed=embed)

    @commands.cooldown(rate=5, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def hug(self, ctx: commands.Context, user: discord.Member = None, intensity: int = 0):
        """Because everyone likes hugs"""
        if user is None:
            user = ctx.author
        elif user == self.bot.user:
            await ctx.send("<:huggers:602823825880514561>")
            return

        async with ctx.typing():
            emojis = config.hug_emojis
            if user != ctx.author:
                self.hugs_repo.do_hug(giver_id=ctx.author.id, receiver_id=user.id)

            user_str = discord.utils.escape_markdown(user.display_name).replace("@", "@ ")

        if 0 <= intensity < len(emojis):
            await ctx.send(emojis[intensity] + f" **{user_str}**")
        else:
            await ctx.send(choice(emojis) + f" **{user_str}**")

    @hug.error
    async def hug_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(utils.fill_message("member_not_found", user=ctx.author.id))
        else:
            print(error)
