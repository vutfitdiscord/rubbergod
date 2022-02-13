import asyncio
import copy
from io import BytesIO
import discord
from discord.ext import commands
import json

from config.app_config import config
from config import cooldowns
from features.git import Git
import utils


class Help(commands.Cog):
    """Help command"""

    def __init__(self, bot):
        self.bot = bot
        self.git = Git()

    def command_details(self, prefix: str, command: commands.Command):
        return {
            "command": f"{prefix}{command.name}",
            "signature": command.signature,
            "description": command.brief,
            "aliases": command.aliases,
        }

    def command_help(self, ctx: commands.Context, command: commands.Command):
        """Generate help for commands and subcommands"""
        current_page = list()
        prefix = config.default_prefix
        if type(command) == commands.Group:
            # group command without invoked subcommand is separate command
            # e.g. karma, reviews
            if command.usage is not None:
                current_page.append(self.command_details(prefix, command))
            key_prefix = f"{prefix}{command.name} "
            for subcommand in command.commands:
                for check in subcommand.checks:
                    try:
                        if not check(ctx):
                            break
                    except Exception:
                        break
                else:
                    current_page.append(self.command_details(key_prefix, subcommand))
        elif not command.parent:
            current_page.append(self.command_details(prefix, command))
        return current_page


    def generate_pages(self, ctx: commands.Context):
        """Generate pages for help. Page per cog. Including subcommands and applying commands checks"""
        pages = list()
        for name, cog in self.bot.cogs.items():
            current_page = list()
            for command in cog.walk_commands():
                for check in command.checks:
                    try:
                        if not check(ctx):
                            break
                    except Exception:
                        break
                else:
                    current_page += self.command_help(ctx, command)
            if current_page:
                pages.append({
                    "commands": current_page,
                    "description": cog.description,
                    "groupName": name
                })

        return pages

    def generate_embed(self, page):
        embed = discord.Embed(title="Nápověda", color=0xeee657)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        self.add_fields(embed, page["commands"])
        return embed

    def add_fields(self, embed, items):
        """Add fields to embed help. 
        
        param: items: List of dict with commands
        """
        for item in items:
            value = ''
            name = f'{item["command"]}'
            if item["signature"] and item["signature"] != ' ':
                name += f' `{item["signature"]}`'
            if item["aliases"]:
                value += f'**Alias: **{", ".join(item["aliases"])}\n'
            value += item["description"] if item["description"] else ''
            embed.add_field(name=name, value=value if value else None, inline=False)

    @commands.Cog.listener()
    async def on_message(self, message: discord.message):
        """Sending commands help to grillbot"""
        if message.author.id not in config.grillbot_ids:
            return

        lines = message.content.split('\n')
        if not (lines[0] == '```json' and lines[-1] == '```'):
            return
        lines = lines[1:-1]
        content = '\n'.join(lines)
        request = json.loads(content)
        if "method" not in request or request["method"] != "help":
            await message.reply("Unsupported method")
            return
        param = request["parameters"]
        # mock ctx
        mock_message = copy.copy(message)
        mock_message.author = self.bot.get_user(param["user_id"])
        ctx = commands.Context(
            prefix=config.default_prefix,
            message=mock_message,
        )
        if "command" in param and param["command"] != None:
            command = self.bot.get_command(param["command"])
            if not command:
                await message.reply("Command not found")
                return
            help = {}
            for check in command.checks:
                try:
                    if not check(ctx):
                        break
                except Exception:
                    break
            else:
                help = self.command_help(ctx, command)
        else: # return help for all commands
            help = self.generate_pages(ctx)
        help_json = json.dumps(help)
        with BytesIO(bytes(help_json, 'utf-8')) as file_binary:
            await message.reply(file=discord.File(fp=file_binary, filename="help.json"))

    @cooldowns.default_cooldown
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
        page_num = 1

        pages = self.generate_pages(ctx)
        embed = self.generate_embed(pages[0])

        pages_total = len(pages)

        commit = f"Commit {self.git.hash()}"
        footer_text = commit
        if pages_total > 1:
            footer_text = f"Strana {page_num}/{pages_total} | {commit}"
        embed.set_footer(text=footer_text, icon_url=ctx.author.avatar_url)

        message = await ctx.reply(embed=embed)

        await utils.add_pagination_reactions(message, pages_total)

        while True:

            def check(reaction, user):
                return reaction.message.id == message.id and not user.bot

            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=300.0)
            except asyncio.TimeoutError:
                return
            emoji = str(reaction.emoji)
            if emoji in ["⏪", "◀", "▶", "⏩"] and user.id == ctx.author.id:
                page_num = utils.pagination_next(emoji, page_num, pages_total)
                embed.clear_fields()
                self.add_fields(embed, pages[page_num - 1]["commands"])
                embed.set_footer(text=f"Strana {page_num}/{pages_total} | {commit}")
                await message.edit(embed=embed)
            try:
                await message.remove_reaction(emoji, user)
            except discord.errors.Forbidden:
                pass


def setup(bot):
    bot.add_cog(Help(bot))
