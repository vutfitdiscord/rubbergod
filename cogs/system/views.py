import logging

import disnake

from buttons.base import BaseView
from permissions.permission_check import PermissionsCheck
from rubbergod import Rubbergod

from . import features
from .messages_cz import MessagesCZ

rubbergod_logger = logging.getLogger("rubbergod")


class View(BaseView):
    def __init__(self, bot: Rubbergod, cogs: list[list[tuple[str, str]]]):
        super().__init__()
        self.bot = bot
        self.count = len(cogs)
        self.cogs = cogs
        self.message: disnake.Message
        self.selects = []

        for i in range(self.count):
            self.selects.append(Dropdown(bot, self, cogs[i]))
            self.add_item(self.selects[i])

    @disnake.ui.button(label="Reload off", style=disnake.ButtonStyle.secondary)
    async def reload_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        for i in range(len(self.selects)):
            self.selects[i].reload = not self.selects[i].reload

        if self.selects[0].reload:
            button.style = disnake.ButtonStyle.green
            button.label = "Reload on"
        else:
            button.style = disnake.ButtonStyle.secondary
            button.label = "Reload off"

        await inter.response.edit_message(view=self)

    async def on_timeout(self) -> None:
        try:
            await self.message.edit(view=None)
        except Exception:
            pass

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        if PermissionsCheck.is_bot_admin(inter):
            return True
        return False


class Dropdown(disnake.ui.Select):
    def __init__(self, bot: Rubbergod, view: View, cogs: list[tuple[str, str]]):
        self.bot = bot
        self._view = view
        self.cogs: list[tuple[str, str]] = cogs
        self.reload = False
        self.message: disnake.Message
        self.unloadable_cogs = ["system"]

        super().__init__(
            placeholder=self.get_initials(),
            min_values=1,
            max_values=len(self.cogs),
            options=self.create_select(),
        )

    def unloaded_cogs(self) -> list[str]:
        """Return list of unloaded paths to cogs"""
        cogs = [cog for cog, _ in self.cogs]
        loaded = [cog.lower() for cog in self.bot.cogs if cog.lower() in cogs]
        return list(set(cogs) - set(loaded))

    def get_initials(self) -> str:
        """Creates placeholder for selects from names of cogs."""
        first = self.cogs[0][0]
        last = self.cogs[len(self.cogs) - 1][0]
        return f"{first.title()} - {last.title()}"

    def create_select(self) -> list[disnake.SelectOption]:
        """Creates one singular select from cogs"""
        options = []
        cogs = [cog for cog, _ in self.cogs]
        loaded = [cog.lower() for cog in self.bot.cogs if cog.lower() in cogs]
        loaded.sort()

        for cog, file in self.cogs:
            if cog in loaded:
                options.append(disnake.SelectOption(label=cog.title(), value=cog, emoji="✅"))
            else:
                options.append(disnake.SelectOption(label=cog.title(), value=cog, emoji="❌"))
        return options

    async def callback(self, inter: disnake.MessageInteraction) -> None:
        """React to user selecting cog(s)."""
        await inter.response.defer()
        if not PermissionsCheck.is_bot_admin(inter):
            return

        unloadable = [cog for cog in self.unloadable_cogs if cog in self.values]
        if unloadable:
            await inter.followup.send(MessagesCZ.cog_not_unloadable(cogs=", ".join(unloadable)))
            self.options = self.create_select()
            for cog in unloadable:
                self.values.remove(cog)

        if not self.reload:
            for cog in self.values:
                if cog in self.unloaded_cogs():
                    try:
                        self.bot.load_extension(f"cogs.{cog}")
                        rubbergod_logger.info(MessagesCZ.success_load(cog=cog))
                    except Exception as e:
                        await inter.send(f"Loading error\n`{e}`")
                else:
                    try:
                        self.bot.unload_extension(f"cogs.{cog}")
                        rubbergod_logger.info(MessagesCZ.success_unload(cog=cog))
                    except Exception as e:
                        await inter.send(f"Unloading error\n`{e}`")
        else:
            cogs = set()
            for cog in self.values:
                try:
                    self.bot.reload_extension(f"cogs.{cog}")
                    rubbergod_logger.info(MessagesCZ.success_reload(cog=cog))
                    cogs.add(cog)
                except Exception as e:
                    await inter.send(f"Reloading error\n`{e}`")
            if cogs:
                await inter.send(MessagesCZ.success_reload(cog=", ".join(cogs)))

        self.options = self.create_select()
        await self.message.edit(embed=features.create_embed(self.bot), view=self._view)
