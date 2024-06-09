import disnake

from rubbergod import Rubbergod

from . import features
from .messages_cz import MessagesCZ


class IconSelect(disnake.ui.Select):
    def __init__(self, bot: Rubbergod, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bot = bot

    async def callback(self, inter: disnake.MessageInteraction):
        await inter.response.defer(ephemeral=True)
        [choice] = self.values
        icon = disnake.utils.get(inter.guild.roles, id=int(choice))
        if icon is None:
            await inter.edit_original_response(MessagesCZ.fail_icon)
            return
        user = inter.user
        if await features.can_assign(icon, user):
            await inter.edit_original_response(
                MessagesCZ.set_success(
                    user=inter.user, icon=features.icon_emoji(self.bot, icon) or features.icon_name(icon)
                ),
                view=None,
            )
            await features.do_set_icon(icon, user)
        else:
            await inter.edit_original_response(MessagesCZ.no_permission)
