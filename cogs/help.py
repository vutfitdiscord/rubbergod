import asyncio
import discord
from discord.ext import commands

from config import app_config as config, messages
from features.git import Git

config = config.Config


class Help(commands.Cog):
    """Help command"""

    def __init__(self, bot):
        self.bot = bot
        self.git = Git()

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
                        # group command without invoked subcommand is separate command
                        # e.g. karma, reviews
                        if command.usage is not None:
                            current_page[f"{prefix}{command.name} {command.signature}"] = command.brief
                        key_prefix = f"{prefix}{command.name}"
                        for subcommand in command.commands:
                            for check in subcommand.checks:
                                try:
                                    if not check(ctx):
                                        break
                                except Exception:
                                    break
                            else:
                                key = f"{key_prefix} {subcommand.name} {subcommand.signature}"
                                current_page[key] = subcommand.brief
                    elif not command.parent:
                        current_page[f"{prefix}{command.name} {command.signature}"] = command.brief
            if current_page:
                pages.append(current_page)

        return pages

    def generate_embed(self, page):
        embed = discord.Embed(title="Nápověda", color=0xeee657)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        for key, value in page.items():
            embed.add_field(name=key, value=value, inline=False)
        return embed


    @commands.cooldown(rate=2, per=20.0, type=commands.BucketType.user)
    @commands.command(aliases=['god'], brief="Nápověda")
    async def help(self, ctx: commands.Context, *command):
        # Subcommand help
        command = ' '.join(command)
        if command:
            command_obj = self.bot.get_command(command)
            if not command_obj:
                await ctx.send(f"Žádný příkaz jako `{command}` neexistuje.")
            else:
                # if command group, show all possible subcommands
                if type(command_obj) == commands.Group:
                    subcommands = []
                    if command_obj.usage is not None:
                        subcommands.append(command_obj.usage.replace('[', '').replace(']', ''))
                    subcommands += [subcommand.name for subcommand in command_obj.commands]
                    text = f"`{config.default_prefix}{command_obj.name} [{', '.join(subcommands)}]`"
                else:
                    text = f"`{config.default_prefix}{command_obj} {command_obj.signature}`"
                if command_obj.description:
                    text += f"\n{command_obj.description}"
                elif command_obj.brief:
                    text += f"\n{command_obj.brief}"
                await ctx.send(text)
            return

        # General help
        page_num = 0

        pages = self.generate_pages(ctx)
        embed = self.generate_embed(pages[0])

        pages_total = len(pages)

        commit = f"Commit {self.git.hash()}"
        footer_text = commit
        if pages_total > 1:
            footer_text = f"Strana {page_num + 1}/{pages_total} | {commit}"
        embed.set_footer(text=footer_text, icon_url=ctx.author.avatar_url)

        message = await ctx.send(embed=embed)

        if pages_total <= 1:
            return
        
        await message.add_reaction("⏪")
        await message.add_reaction("◀")
        await message.add_reaction("▶")
        await message.add_reaction("⏩")

        while True:

            def check(reaction, user):
                return reaction.message.id == message.id and not user.bot

            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300.0)
            except asyncio.TimeoutError:
                return
            emoji = str(reaction.emoji)
            if emoji in ["⏪", "◀", "▶", "⏩"] and user.id == ctx.author.id:
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
                embed.clear_fields()
                for key, value in pages[page_num].items():
                    embed.add_field(name=key, value=value, inline=False)
                embed.set_footer(text=f"Strana {page_num + 1}/{pages_total} | {commit}")
                await message.edit(embed=embed)
            try:
                await message.remove_reaction(emoji, user)
            except discord.errors.Forbidden:
                pass


def setup(bot):
    bot.add_cog(Help(bot))
