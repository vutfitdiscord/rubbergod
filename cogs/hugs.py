from random import choice
from typing import Iterable

import discord
from discord.ext import commands

import utils
from config import app_config
from config import app_config as config
from repository.database.hugs import HugsTable
from repository.hugs_repo import HugsRepository

config = app_config.Config


class Hugs(commands.Cog):
    """
    Hugging commands.
    """

    def __init__(self, bot):
        self.bot = bot
        self.hugs_repo = HugsRepository()

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def hugboard(self, ctx: commands.Context):
        """
        Overall hugging stats.
        """
        with ctx.typing():
            hug_data = self.hugs_repo.get_top_all()
            embed = self.format_stats(ctx, hug_data)

        await ctx.send(embed=embed)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def huggers(self, ctx: commands.Context):
        """
        Get the biggest huggers.
        """
        pass

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def hugged(self, ctx: commands.Context):
        """
        Get the most hugged.
        """
        pass

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def hugs(self, ctx: commands.Context):
        """
        Get your lovely hug stats.
        """
        pass

    def format_stats(self, ctx: commands.Context, sql_data: Iterable) -> discord.Embed:
        guild = self.bot.get_guild(config.guild_id)
        if not guild:
            guild = ctx.guild

        content = []
        for i, entry in enumerate(sql_data):  # type: int, HugsTable
            user = guild.get_member(entry.member_id)
            username = f"**{discord.utils.escape_markdown(user.name)}**" if user else "*User left*"

            content.append(
                "{i} - {user_name}: {given}/{received}".format(
                    i=i + 1, user_name=username, given=entry.given, received=entry.received,
                )
            )

        if guild == config.guild_id:
            emoji_left, emoji_right = "<:peepoHugger:759846963456770069>", "<:huggers:602823825880514561>"
        else:
            # not in configured guild, default to normal emojis
            emoji_left = emoji_right = ":people_hugging:"

        embed = discord.Embed(
            title=f"{emoji_left}Top Huggers{emoji_right}", description="\n" + "\n".join(content),
        )
        utils.add_author_footer(embed, ctx, additional_text=("Hint: dostal/rozdal",))

        return embed

    @commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
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


def setup(bot):
    bot.add_cog(Hugs(bot))
