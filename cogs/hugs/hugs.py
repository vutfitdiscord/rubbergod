from random import choice

import discord
from discord.ext import commands

import utils
from config import app_config
from repository.hugs_repo import HugsRepository
from .menus import get_hugboard_menu, get_top_huggers_menu, get_top_hugged_menu
from .. import room_check

config = app_config.Config


class Hugs(commands.Cog):
    """
    Hugging commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.hugs_repo = HugsRepository()
        self.check = room_check.RoomCheck(bot)

    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def hugboard(self, ctx: commands.Context):
        """
        Overall hugging stats.
        """
        async with ctx.typing():
            menu = get_hugboard_menu(
                base_embed=discord.Embed(
                    title="{0} HUGBOARD {0}".format(utils.get_emoji(ctx.message.guild, "peepoHugger"))
                )
            )

        await self.check.botroom_check(ctx.message)
        await menu.start(ctx)

    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def huggers(self, ctx: commands.Context):
        """
        Get the biggest huggers.
        """
        async with ctx.typing():
            menu = get_top_huggers_menu(
                base_embed=discord.Embed(
                    title="{0} TOP HUGGERS {0} ".format(utils.get_emoji(ctx.message.guild, "peepoHugger"))
                )
            )
        await self.check.botroom_check(ctx.message)
        await menu.start(ctx)

    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def hugged(self, ctx: commands.Context):
        """
        Get the most hugged.
        """
        async with ctx.typing():
            menu = get_top_hugged_menu(
                base_embed=discord.Embed(
                    title="{0} TOP HUGGED {0} ".format(utils.get_emoji(ctx.message.guild, "peepoHugger"))
                )
            )

        await self.check.botroom_check(ctx.message)
        await menu.start(ctx)

    @commands.cooldown(rate=5, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def hugs(self, ctx: commands.Context, user: discord.User = None):
        """
        Get your lovely hug stats.
        """
        if user is None:
            user = ctx.author

        async with ctx.typing():
            stats = self.hugs_repo.get_members_stats(user.id)
            positions = self.hugs_repo.get_member_position(stats)
            avg_position = int((positions[0] + positions[1]) // 2)

            embed = discord.Embed(
                title="{0} Your Lovely Hug Stats {0}".format(
                    utils.get_emoji(ctx.message.guild, "peepoHugger")
                ),
                description=" | ".join(
                    (
                        "**Ranks**",
                        f"Given: **{positions[0]}.**",
                        f"Received: **{positions[1]}.**",
                        f"Avg: **{avg_position}.**",
                    )
                ),
            )

            embed.set_author(name=user.name, icon_url=user.avatar_url)
            utils.add_author_footer(embed, ctx.author)

            if ctx.guild and ctx.guild.id == config.guild_id:
                given_emoji = utils.get_emoji(ctx.message.guild, "peepohugs")
                recv_emoji = utils.get_emoji(ctx.message.guild, "huggers")
            else:
                given_emoji = recv_emoji = ":people_hugging:"

            embed.add_field(name=f"{given_emoji} Given", value=str(stats.given))
            embed.add_field(name=f"{recv_emoji} Received", value=str(stats.received))

        await ctx.send(embed=embed)
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=5, per=60.0, type=commands.BucketType.user)
    @commands.command()
    async def hug(self, ctx: commands.Context, user: discord.User = None, intensity: int = 0):
        """Because everyone likes hugs"""
        if user is None:
            user = ctx.author
        elif user.bot:
            await ctx.send(utils.get_emoji(ctx.message.guild, "huggers"))
            return

        async with ctx.typing():
            emojis = config.hug_emojis
            if user != ctx.author:
                self.hugs_repo.do_hug(giver_id=ctx.author.id, receiver_id=user.id)

            user_str = discord.utils.escape_markdown(user.display_name).replace("@", "@ ")

        if 0 <= intensity < len(emojis):
            await ctx.send(f"{emojis[intensity]} **{user_str}**")
        else:
            await ctx.send(f"{choice(emojis)} **{user_str}**")

    @hug.error
    async def hug_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(utils.fill_message("member_not_found", user=ctx.author.id))
        else:
            print(error)
