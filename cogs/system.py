from disnake.ext import commands
from features.git import Git
from disnake.message import Message
import utils
import disnake
import numpy as np
import math
from config.messages import Messages


class SystemView(disnake.ui.View):
    def __init__(self, bot, count, cogs):
        super().__init__()
        self.bot = bot
        self.count = count
        self.cogs = cogs
        self.message = ""
        self.selects = []

        for i in range(count):
            self.selects.append(Dropdown(bot, self, cogs[i]))
            self.add_item(self.selects[i])

    @disnake.ui.button(label="Reload off", style=disnake.ButtonStyle.secondary)
    async def reload_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        for i, cogs in enumerate(self.selects):
            self.selects[i].reload = not self.selects[i].reload

        if self.selects[0].reload:
            button.style = disnake.ButtonStyle.green
            button.label = "Reload on"
        else:
            button.style = disnake.ButtonStyle.secondary
            button.label = "Reload off"

        await inter.response.edit_message(view=self)

    async def on_timeout(self):
        lenght = len(self.children)
        for x in range(lenght):
            self.remove_item(self.children[0])
        await self.message.edit(view=self)


class Dropdown(disnake.ui.Select):
    def __init__(self, bot, view, cogs):
        self.bot = bot
        self._view = view
        self.cogs = cogs
        self.reload = False
        self.msg = ""
        self.unloadable_cogs = ["system"]

        super().__init__(
            placeholder=self.get_initials(),
            min_values=1,
            max_values=len(self.cogs[0]),
            options= self.create_select()
        )

    def get_initials(self):
        """Creates placeholder for selects from names of cogs."""
        first = self.cogs[0][0].capitalize()
        last = self.cogs[0][len(self.cogs)-1].capitalize()
        return f"{first} - {last}"

    def create_select(self):
        """Creates one singular select from cogs"""
        options = []
        dict_of_cogs = dict(zip(self.cogs[0], self.cogs[1]))
        val_list = list(dict_of_cogs.values())
        key_list = list(dict_of_cogs.keys())

        loaded = []
        for value in val_list:
            if value in self.bot.cogs:
                position = val_list.index(value)
                loaded.append(key_list[position])

        for cog in dict_of_cogs:
            cogname = cog.capitalize()
            if cog.lower() in loaded:
                options.append(disnake.SelectOption(label=cogname, value=cog, emoji="✅"))
            else:
                options.append(disnake.SelectOption(label=cogname, value=cog, emoji="❌"))
        return options

    def create_cog_lists(self):
        cog_files = utils.get_all_cogs().keys()

        # list out keys and values separately
        key_list = self.cogs[0]
        val_list = self.cogs[1]
        bot_cogs = [cog for cog in self.bot.cogs]

        loaded = []
        for value in val_list:
            if value in bot_cogs:
                position = val_list.index(value)
                loaded.append(key_list[position])

        unloaded = list(set([cog.lower() for cog in cog_files]) - set(loaded))
        loaded.sort()
        unloaded.sort()
        return (loaded, unloaded)

    def create_embed(self):
        embed = disnake.Embed(title="Cogs information and loading", colour=disnake.Colour.red())

        key_list = list(utils.get_all_cogs().keys())
        val_list = list(utils.get_all_cogs().values())
        bot_cogs = [cog for cog in self.bot.cogs]

        loaded = []
        for value in val_list:
            if value in bot_cogs:
                position = val_list.index(value)
                loaded.append(key_list[position])

        unloaded = list(set([cog.lower() for cog in key_list]) - set(loaded))

        loaded.sort()
        unloaded.sort()

        cog_loaded = ""
        for cog in loaded:
            cog_loaded += f"✅ {cog.capitalize()}\n\n"

        cog_unloaded = ""
        for cog in unloaded:
            cog_unloaded += f"❌ {cog.capitalize()}\n\n"

        cog_list = cog_loaded + cog_unloaded
        cog_sum = len(loaded) + len(unloaded)

        embed.add_field(
            name="Loaded/Unloaded/All",
            value=f"**{len(loaded)} / {len(unloaded)} / {cog_sum}**",
            inline=False
        )
        embed.add_field(
            name="Cog list:",
            value=cog_list,
            inline=False
        )
        return embed

    async def callback(self, inter: disnake.MessageInteraction):
        """React to user selecting cog(s)."""
        await inter.response.defer()

        unloaded = self.create_cog_lists()[1]

        for cog in self.unloadable_cogs:
            if cog in self.values:
                await inter.send(utils.fill_message("cog_cannot_be_unloadable", cog=cog))
                self.options = self.create_select()
                self.values.remove(cog)

        if not self.reload:
            for cog in self.values:
                if cog in unloaded:
                    try:
                        self.bot.load_extension(f"cogs.{cog}")
                        print(utils.fill_message("cog_loaded", cog=cog))
                    except Exception as e:
                        await inter.send(f"Loading error\n`{e}`")
                else:
                    try:
                        self.bot.unload_extension(f"cogs.{cog}")
                        print(utils.fill_message("cog_unloaded", cog=cog))
                    except Exception as e:
                        await inter.send(f"Unloading error\n`{e}`")
        else:
            for cog in self.values:
                try:
                    self.bot.reload_extension(f"cogs.{cog}")
                    print(utils.fill_message("cog_reloaded", cog=cog))
                except Exception as e:
                    await inter.send(f"Reloading error\n`{e}`")

        self.options = self.create_select()
        await self.msg.edit(embed=self.create_embed(), view=self._view)


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

    async def create_selects(self):
        """Slices dictionary of all cogs to chunks for select."""
        cog_files = list(utils.get_all_cogs().keys())
        cog_names = list(utils.get_all_cogs().values())
        all_selects = []

        # 25 is max number of options for one select
        chunks = math.ceil(len(cog_files)/25)
        cog_files = [x.tolist() for x in np.array_split(cog_files, chunks)]
        cog_names = [x.tolist() for x in np.array_split(cog_names, chunks)]
        for i in range(0, chunks):
            all_selects.append([cog_files[i], cog_names[i]])

        return all_selects

    @commands.check(utils.is_bot_admin)
    @commands.slash_command(name="cogs", description="Manipulate with cogs")
    async def cogs(self, inter: disnake.ApplicationCommandInteraction):
        """
        Creates embed with button and select(s) to load/unload/reload cogs.

        Max number of cogs can be 100 (4x25).
        """
        selects = await self.create_selects()
        view = SystemView(self.bot, len(selects[0]), selects)
        embed = Dropdown.create_embed(self)

        await inter.send(embed=embed, view=view)
        message = await inter.original_message()

        # pass message object to classes
        view.message = message
        for i, cogs in enumerate(selects):
            view.selects[i].msg = message

    @pull.error
    @cogs.error
    async def on_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send("Missing argument.")
            return True
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
