from functools import lru_cache
from random import choice

import discord
from discord.ext import commands

import utils
from config.app_config import config
from config import cooldowns
from repository.hugs_repo import HugsRepository
from .menus import get_hugboard_menu, get_top_huggers_menu, get_top_hugged_menu
from .. import room_check


class Hugs(commands.Cog):
    """
    Hugging commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.hugs_repo = HugsRepository()
        self.check = room_check.RoomCheck(bot)

    @lru_cache(5)
    def get_default_emoji(self, emoji: str):
        return utils.get_emoji(self.bot.get_guild(config.guild_id), emoji)

    @cooldowns.long_cooldown
    @commands.command()
    async def hugboard(self, ctx: commands.Context):
        """
        Overall hugging stats.
        """
        async with ctx.typing():
            menu = get_hugboard_menu(
                base_embed=discord.Embed(
                    title="{0} HUGBOARD {0}".format(
                        self.get_default_emoji("peepoHugger") or ""
                    )
                )
            )

        await self.check.botroom_check(ctx.message)
        await menu.start(ctx)

    @cooldowns.long_cooldown
    @commands.command()
    async def huggers(self, ctx: commands.Context):
        """
        Get the biggest huggers.
        """
        async with ctx.typing():
            menu = get_top_huggers_menu(
                base_embed=discord.Embed(
                    title="{0} TOP HUGGERS {0} ".format(
                        self.get_default_emoji("peepoHugger") or ""
                    )
                )
            )
        await self.check.botroom_check(ctx.message)
        await menu.start(ctx)

    @cooldowns.long_cooldown
    @commands.command()
    async def hugged(self, ctx: commands.Context):
        """
        Get the most hugged.
        """
        async with ctx.typing():
            menu = get_top_hugged_menu(
                base_embed=discord.Embed(
                    title="{0} TOP HUGGED {0} ".format(
                        self.get_default_emoji("peepoHugger") or ""
                    )
                )
            )

        await self.check.botroom_check(ctx.message)
        await menu.start(ctx)

    @cooldowns.long_cooldown
    @commands.command()
    async def hugs(self, ctx: commands.Context, user: discord.Member = None):
        """
        Get your lovely hug stats.
        """
        if user is None or user == ctx.author:
            user = ctx.author
            user_str = utils.get_username(user)
            title = "{0} Your Lovely Hug Stats {0}"
        else:
            user_str = utils.get_username(user)
            title = f"{{0}} {user_str}'s Lovely Hug Stats {{0}}"

        async with ctx.typing():
            stats = self.hugs_repo.get_members_stats(user.id)
            positions = self.hugs_repo.get_member_position(stats)
            avg_position = int((positions[0] + positions[1]) // 2)

            embed = discord.Embed(
                title=title.format(
                    self.get_default_emoji("peepoHugger") or ""
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

            embed.set_author(name=user_str, icon_url=user.avatar_url)
            utils.add_author_footer(embed, ctx.author)

            given_emoji = self.get_default_emoji("peepohugs") or ""
            recv_emoji = self.get_default_emoji("huggers") or ""

            embed.add_field(name=f"{given_emoji} Given", value=str(stats.given))
            embed.add_field(name=f"{recv_emoji} Received", value=str(stats.received))

        await ctx.send(embed=embed)
        await self.check.botroom_check(ctx.message)

    @cooldowns.short_cooldown
    @commands.command()
    async def hug(self, ctx: commands.Context, user: discord.Member = None, intensity: int = 0):
        """Because everyone likes hugs"""
        if user is None:
            user = ctx.author
        elif user.bot:
            await ctx.send(self.get_default_emoji("huggers") or ":people_hugging:")
            return

        async with ctx.typing():
            emojis = config.hug_emojis
            if user != ctx.author:
                self.hugs_repo.do_hug(giver_id=ctx.author.id, receiver_id=user.id)

            user_str = utils.get_username(user)

        if 0 <= intensity < len(emojis):
            await ctx.send(f"{emojis[intensity]} **{user_str}**")
        else:
            await ctx.send(f"{choice(emojis)} **{user_str}**")

    @hugs.error
    @hug.error
    async def hug_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(utils.fill_message("member_not_found", user=ctx.author.id))
        else:
            print(error)
