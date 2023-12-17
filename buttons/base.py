import datetime
import traceback
from typing import Optional

import disnake

import utils
from config.app_config import config
from database.stats import ErrorEvent


class BaseView(disnake.ui.View):

    error_log = None

    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)

    async def on_error(self, error, item: disnake.ui.Item, interaction: disnake.MessageInteraction):
        # import here to avoid circular imports
        from buttons.error import ErrorView
        from features.error import ErrorLogger

        if self.error_log is None:
            self.error_log = ErrorLogger(interaction.bot)
        await self.error_log.ignore_errors(interaction, error)

        channel_out = interaction.bot.get_channel(config.bot_dev_channel)
        embed = self.error_log.create_embed(
            command="on_button_error",
            args=interaction.data.custom_id,
            author=interaction.author,
            guild=interaction.guild,
            jump_url=interaction.message.jump_url,
            extra_fields={
                "Message content": interaction.message.content,
                "Expirace (UTC)": interaction.expires_at.strftime("%Y-%m-%d %H:%M:%S"),
                "Item": item,
            }
        )
        error_log = ErrorEvent.log(
            event_name="on_button_error",
            cog=self.__class__.__name__,
            datetime=datetime.datetime.now(),
            user_id=interaction.author.id,
            args=str(item),
            exception=type(error).__name__,
            traceback="\n".join(traceback.format_exception(type(error), error, error.__traceback__)),
        )
        utils.add_author_footer(
            embed,
            author=interaction.author,
            additional_text=[f"ID: {error_log.id}"]
        )
        await channel_out.send(embed=embed, view=ErrorView())

        # remove interactions because of error
        await interaction.message.edit(view=None)
