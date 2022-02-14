from disnake.ext import commands
from features.git import Git
from disnake.message import Message
import utils
from config.messages import Messages


class System(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.git = Git()

        self.unloadable_cogs = ["system"]

    @commands.group(pass_context=True)
    async def git(self, ctx: commands.Context):
        pass

    @git.command(brief=Messages.git_pull_brief)
    @commands.check(utils.is_bot_admin)
    async def pull(self, ctx: commands.Context):
        message: Message = await ctx.send("Pulling")

        pull_result = await self.git.pull()
        pull_parts = utils.cut_string(pull_result, 1900)

        await message.edit(content=f"```{pull_parts[0]}```")

        for part in pull_parts[1:]:
            await ctx.send(f"```{part}```")

    @commands.command(brief=Messages.cog_load_brief)
    @commands.check(utils.is_bot_admin)
    async def load(self, ctx: commands.Context, extension: str):
        """Load cog"""
        try:
            self.bot.load_extension(f"cogs.{extension}")
            print(f'{extension} loaded')
            await ctx.send(utils.fill_message("cog_loaded", cog=extension))
        except Exception as e:
            await ctx.send(f"Loading error\n`{e}`")

    @commands.command(brief=Messages.cog_unload_brief)
    @commands.check(utils.is_bot_admin)
    async def unload(self, ctx: commands.Context, extension: str):
        """Unload cog"""
        if extension in self.unloadable_cogs:
            await ctx.send(utils.fill_message("cog_cannot_be_unloadable", cog=extension))
            return

        try:
            self.bot.unload_extension(f"cogs.{extension}")
            print(f'{extension} unloaded')
            await ctx.send(utils.fill_message("cog_unloaded", cog=extension))
        except Exception as e:
            await ctx.send(f"Unloading error\n`{e}`")

    @commands.command(brief=Messages.cog_reload_brief)
    @commands.check(utils.is_bot_admin)
    async def reload(self, ctx: commands.Context, extension: str):
        """Reload cog"""
        try:
            self.bot.reload_extension(f"cogs.{extension}")
            print(f'{extension} reloaded')
            await ctx.send(utils.fill_message("cog_reloaded", cog=extension))
        except Exception as e:
            await ctx.send(f"Reloading error\n`{e}`")

    @commands.command(aliases=["extensions"], brief=Messages.cogs_brief)
    @commands.check(utils.is_bot_admin)
    async def cogs(self, ctx: commands.Context):
        """Return loaded cogs"""
        cogs = self.bot.cogs
        cog_names = []
        for cog in cogs:
            cog_names.append(str(cog))
        await ctx.send(cog_names)

    @pull.error
    @load.error
    @unload.error
    @reload.error
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send("Missing argument.")
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))
        if isinstance(error, commands.errors.CommandInvokeError):
            if isinstance(error.__cause__, commands.errors.ExtensionAlreadyLoaded):
                await ctx.send(utils.fill_message("cog_is_loaded", cog=error.__cause__.name))
            elif isinstance(error.__cause__, commands.errors.ExtensionNotLoaded):
                await ctx.send(utils.fill_message("cog_is_unloaded", cog=error.__cause__.name))


def setup(bot):
    bot.add_cog(System(bot))
