"""
Cog containing help command. Only shows commands that user has access to
and are context commands.
"""

import copy

import disnake
from disnake.ext import commands

import utils
from buttons.embed import EmbedView
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from features.git import Git


class Help(Base, commands.Cog):
    """Help command"""

    def __init__(self, bot: commands.Bot):
        super().__init__()
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
        prefix = self.config.default_prefix
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

    async def api(self, message: commands.Context, params: list):
        """Sending commands help to grillbot"""
        mock_message = copy.copy(message)
        mock_view = commands.view.StringView("")
        mock_message.author = self.bot.get_user(params.get("user_id"))
        ctx = commands.Context(
            bot=self.bot,
            view=mock_view,
            prefix=self.config.default_prefix,
            message=mock_message,
        )
        if "command" in params and params["command"] is not None:
            if params["command"] == "slash_commands":
                res = {}
                for slash in self.bot.slash_commands:
                    res[slash.name] = {
                        "id": utils.get_command_id(self, slash.name),
                        "children": list(slash.children.keys())
                    }
                return 0, res
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
        else:  # return help for all commands
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
                await ctx.send(Messages.help_command_not_found(command=command[:1024]))
            else:
                # if command group, show all possible subcommands
                if type(command_obj) == commands.Group:
                    subcommands = []
                    if command_obj.usage is not None:
                        subcommands.append(command_obj.usage.replace('[', '').replace(']', ''))
                    subcommands += [subcommand.name for subcommand in command_obj.commands]
                    text = f"`{self.config.default_prefix}{command_obj.name} [{', '.join(subcommands)}]`"
                else:
                    text = f"`{self.config.default_prefix}{command_obj} {command_obj.signature}`"
                if command_obj.description:
                    text += f"\n{command_obj.description}"
                elif command_obj.brief:
                    text += f"\n{command_obj.brief}"
                await ctx.send(text)
            return

        # General help
        pages = self.generate_pages(ctx)
        pages_total = len(pages)

        embeds = []
        for idx, page in enumerate(pages):
            embed = self.generate_embed(page)
            if pages_total > 1:
                footer_text = f"Strana {idx+1}/{pages_total}"
            embed.set_footer(text=footer_text, icon_url=ctx.author.display_avatar.url)
            embeds.append(embed)

        view = EmbedView(ctx.author, embeds, perma_lock=True)
        view.message = await ctx.reply(embed=embeds[0], view=view)


def setup(bot):
    bot.add_cog(Help(bot))
