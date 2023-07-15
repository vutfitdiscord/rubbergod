import traceback
from typing import Optional

import disnake
from disnake.ext import commands

import utils
from config.app_config import config
from config.messages import Messages
from features.error import ErrorLogger
from permissions import permission_check


class BaseView(disnake.ui.View):

    def __init__(self, *, timeout: Optional[float] = 180):
        self.log_error = ErrorLogger()
        super().__init__(timeout=timeout)

    async def on_error(self, error, item: disnake.ui.Item, interaction: disnake.MessageInteraction):
        if (
            isinstance(error, permission_check.NotHelperPlusError)
            or isinstance(error, permission_check.NotSubmodPlusError)
            or isinstance(error, permission_check.NotModPlusError)
            or isinstance(error, permission_check.NotAdminError)
        ):
            await interaction.response.send_message(error.message, ephemeral=True)
            return

        if isinstance(error, commands.errors.CheckFailure):
            await interaction.response.send_message(
                Messages.missing_perms(user=interaction.author.id),
                ephemeral=True
            )
            return

        channel_out = interaction.bot.get_channel(config.bot_dev_channel)
        embed = self.log_error.create_embed(
            interaction.data.custom_id,
            interaction.message.content,
            interaction.author,
            interaction.guild,
            interaction.message.jump_url,
        )
        embed.add_field(name="Expirace (UTC)", value=interaction.expires_at.strftime("%Y-%m-%d %H:%M:%S"))
        embed.add_field(name="Exception", value=error)
        embed.add_field(name="Item", value=item)
        output = utils.cut_string(str(vars(self)), 1900)
        output[0] = f"View object dump:\n{output[0]}"
        for message in output:
            await channel_out.send(f"```\n{message}```")
        await channel_out.send(embed=embed)
        await self.log_error.send_output(traceback.format_exc(), channel_out)

        # remove interactions because of error
        self.clear_items()
        await self.message.edit(view=self)
