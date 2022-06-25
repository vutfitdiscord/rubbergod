from disnake.ext import commands
from features.git import Git
from disnake.message import Message
import utils
import disnake
import math
from buttons.system import SystemView, Dropdown
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

    def split(self, array, k):
        n = len(array)
        lists = [array[i * (n // k) + min(i, n % k):(i+1) * (n // k) + min(i+1, n % k)] for i in range(k)]
        return lists

    async def create_selects(self):
        """Slices dictionary of all cogs to chunks for select."""
        cog_files = list(utils.get_all_cogs().keys())
        cog_names = list(utils.get_all_cogs().values())
        all_selects = []

        # 25 is max number of options for one select
        chunks = math.ceil(len(cog_files)/25)
        cog_files = list(self.split(cog_files, chunks))
        cog_names = list(self.split(cog_names, chunks))
        for i in range(0, chunks):
            all_selects.append([cog_files[i], cog_names[i]])

        return all_selects

    @commands.check(utils.is_bot_admin)
    @commands.slash_command(name="cogs", description=Messages.cogs_brief)
    async def cogs(self, inter: disnake.ApplicationCommandInteraction):
        """
        Creates embed with button and select(s) to load/unload/reload cogs.

        Max number of cogs can be 100 (4x25).
        """

        selects = await self.create_selects()
        view = SystemView(self.bot, len(selects), selects)
        embed = Dropdown.create_embed(self, inter.author.colour)
        await inter.send(embed=embed, view=view)

        # pass message object to classes
        message = await inter.original_message()
        view.message = message
        for i, cogs in enumerate(selects):
            view.selects[i].msg = message

    @pull.error
    @cogs.error
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.send(utils.fill_message("insufficient_rights", user=ctx.author.id))
            return True
        if isinstance(error, commands.errors.CommandInvokeError):
            if isinstance(error.__cause__, commands.errors.ExtensionAlreadyLoaded):
                await ctx.send(utils.fill_message("cog_is_loaded", cog=error.__cause__.name))
                return True
            elif isinstance(error.__cause__, commands.errors.ExtensionNotLoaded):
                await ctx.send(utils.fill_message("cog_is_unloaded", cog=error.__cause__.name))
                return True


def setup(bot):
    bot.add_cog(System(bot))
