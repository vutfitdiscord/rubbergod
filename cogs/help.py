import asyncio
import discord
from discord.ext import commands

from config import app_config as config, messages
import utils

config = config.Config


class Help(commands.Cog):
    """Help command"""

    def __init__(self, bot):
        self.bot = bot

    def generate_pages(self, ctx):
        """Generate pages for help. Including subcommands and applying commands checks"""
        pages = []
        prefix = config.default_prefix
        for name, cog in self.bot.cogs.items():
            current_page = dict()
            for command in cog.walk_commands():
                for check in command.checks:
                    try:
                        if not check(ctx):
                            break
                    except Exception:
                        break
                else:
                    if type(command) == commands.Group:
                        key = f"{prefix}{command.name}"
                        for subcommand in command.commands:
                            for check in subcommand.checks:
                                try:
                                    if not check(ctx):
                                        break
                                except Exception:
                                    break
                            else:
                                current_page[f"{key} {subcommand.name}"] = subcommand.brief
                    elif not command.parent:
                        current_page[f"{prefix}{command.name}"] = command.brief
            if current_page:
                pages.append(current_page)

        return pages

    def generate_embed(self, page):
        embed = discord.Embed(title="Rubbergod",
            description="Nejlepší a nejúžasnější bot ever.",
            color=0xeee657,
        )
        embed.add_field(name="Autor", value="Toaster#1111")
        for key, value in page.items():
            embed.add_field(name=key, value=value, inline=False)
        return embed


    @commands.cooldown(rate=2, per=60.0, type=commands.BucketType.user)
    @commands.command(aliases=['god'], brief="Show this help")
    async def help(self, ctx: commands.Context, command: str=""):
        page_num = 1

        pages = self.generate_pages(ctx)
        embed = self.generate_embed(pages[0])

        pages_total = len(pages)

        commit = f"Commit {utils.git_hash()}"
        footer_text = commit
        if pages_total > 1:
            footer_text = f"Page {page_num}/{pages_total} | {commit}"
        embed.set_footer(text=footer_text, icon_url=self.bot.user.avatar_url)

        message = await ctx.send(embed=embed)

        if pages_total <= 1:
            return
        
        await message.add_reaction("⏪")
        await message.add_reaction("◀")
        await message.add_reaction("▶")
        await message.add_reaction("⏩")

        while True:

            def check(reaction, user):
                return (
                    reaction.message.id == message.id
                    and str(reaction.emoji) in ["⏪", "◀", "▶", "⏩"]
                    and not user.bot
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300.0)
            except asyncio.TimeoutError:
                return
            emoji = str(reaction.emoji)
            if emoji == "⏪":
                page_num = 0
            elif emoji == "◀":
                page_num -= 1
                if page_num < 0:
                    page_num = pages_total - 1
            elif emoji == "▶":
                page_num += 1
                if page_num >= pages_total:
                    page_num = 0
            elif emoji == "⏩":
                page_num = pages_total - 1
            try:
                await message.remove_reaction(emoji, user)
            except discord.errors.Forbidden:
                pass
            embed.clear_fields()
            for key, value in pages[page_num].items():
                embed.add_field(name=key, value=value, inline=False)
            embed.set_footer(text=f"Page {page_num + 1}/{pages_total} | {commit}")
            await message.edit(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
