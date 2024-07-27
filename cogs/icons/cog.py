"""
Cog implementing dynamic icon system. Users can assign themselves icons from a list of roles.
"""

import disnake
from disnake.ext import commands

import utils
from buttons.general import TrashView
from cogs.base import Base
from rubbergod import Rubbergod

from . import features
from .messages_cz import MessagesCZ
from .views import IconSelect


class Icons(Base, commands.Cog):
    def __init__(self, bot: Rubbergod):
        super().__init__()
        self.bot = bot

    @utils.general.PersistentCooldown(command_name="icon", limit=Base.config.icon_ui_cooldown)
    @commands.slash_command(description=MessagesCZ.icon_brief, guild_ids=[Base.config.guild_id])
    async def icon(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        icon_roles = features.get_icon_roles(inter.guild)
        user = inter.user
        options = [
            disnake.SelectOption(
                label=features.icon_name(icon), value=str(icon.id), emoji=features.icon_emoji(self.bot, icon)
            )
            for icon in icon_roles
            if await features.can_assign(icon, user)
        ]
        # makes it last row so it's always under the dropdown
        view = TrashView(MessagesCZ.icon_delete_id, row=4)
        for row, start_i in enumerate(range(0, len(options), 25)):
            # 25 is the max number of options per select
            component = IconSelect(
                bot=self.bot,
                placeholder=MessagesCZ.choose_icon,
                options=options[start_i : start_i + 25],
                row=row,
            )
            view.add_item(component)
        await inter.edit_original_response(view=view)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id != MessagesCZ.icon_delete_id:
            return
        await features.do_set_icon(None, inter.author)
        await inter.response.send_message(content=MessagesCZ.icon_removed, ephemeral=True)

    async def cog_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, error: Exception
    ) -> bool:
        if isinstance(error, utils.general.PCommandOnCooldown):
            await inter.response.send_message(str(error), ephemeral=True)
            return True
        return False
