import asyncio
import copy
import disnake
from disnake.ext import commands

from config.app_config import config
from config import cooldowns
from config.messages import Messages
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
        embed = disnake.Embed(
            title=Messages.help_title,
            description=Messages.help_description,
            color=0xeee657
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
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

    def api(self, message: commands.Context, params: list):
        """Sending commands help to grillbot"""
        mock_message = copy.copy(message)
        mock_view = commands.view.StringView("")
        mock_message.author = self.bot.get_user(params["user_id"])
        ctx = commands.Context(
            bot=self.bot,
            view=mock_view,
            prefix=config.default_prefix,
            message=mock_message,
        )
        if "command" in params and params["command"] != None:
            command = self.bot.get_command(params["command"])
            if not command:
                return 1, "Command not found"
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
        return 0, help

    @cooldowns.default_cooldown
    @commands.command(aliases=['god'], brief=Messages.help_title)
    async def help(self, ctx: commands.Context, *command):
        # Subcommand help
        command = ' '.join(command)
        if command:
            command_obj = self.bot.get_command(command)
            if not command_obj:
                await ctx.send(utils.fill_message('help_command_not_found', command=command))
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
        embed.set_footer(text=footer_text, icon_url=ctx.author.display_avatar.url)

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
            except disnake.errors.Forbidden:
                pass


def setup(bot):
    bot.add_cog(Help(bot))
