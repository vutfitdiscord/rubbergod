import disnake
import utils


class SystemView(disnake.ui.View):
    def __init__(self, bot, count, cogs):
        super().__init__()
        self.bot = bot
        self.count = count
        self.cogs = cogs
        self.message = None
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
        self.msg = None
        self.unloadable_cogs = ["system"]

        super().__init__(
            placeholder=self.get_initials(),
            min_values=1,
            max_values=len(self.cogs[0]),
            options=self.create_select()
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
        cog_files = list(utils.get_all_cogs().keys())

        # list out keys and values separately
        file_list = self.cogs[0]
        class_list = self.cogs[1]

        loaded = []
        for value in class_list:
            if value in self.bot.cogs:
                position = class_list.index(value)
                loaded.append(file_list[position])

        unloaded = list(set(cog_files) - set(loaded))
        unloaded.sort()
        return unloaded

    def create_embed(self, author_colour):
        embed = disnake.Embed(title="Cogs information and loading", colour=author_colour)

        all_cogs = utils.get_all_cogs()
        class_list = list(all_cogs.values())

        loaded = []
        for value in class_list:
            if value in self.bot.cogs:
                loaded.append(value)

        unloaded = list(set(class_list) - set(loaded))

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
        if utils.is_bot_admin(inter):
            unloaded = self.create_cog_lists()

            for cog in self.unloadable_cogs:
                if cog in self.values:
                    await inter.send(utils.fill_message("cog_not_unloadable", cog=cog))
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
                        await inter.channel.send(utils.fill_message("cog_reloaded", cog=cog))
                    except Exception as e:
                        await inter.send(f"Reloading error\n`{e}`")

            self.options = self.create_select()
            await self.msg.edit(embed=self.create_embed(inter.author.colour), view=self._view)
        else:
            await inter.send(utils.fill_message("insufficient_rights", user=inter.author.id), ephemeral=True)
