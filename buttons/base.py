import traceback

import disnake

from config.app_config import config
import utils


class BaseView(disnake.ui.View):

    async def on_error(self, error, item: disnake.ui.Item, interaction: disnake.MessageInteraction):
        channel_out = interaction.bot.get_channel(config.bot_dev_channel)
        embed = self.log_error.create_embed(
            interaction.data.custom_id,
            interaction.author,
            interaction.guild,
            interaction.message.jump_url,
        )
        embed.add_field(name="Expirace (UTC)", value=interaction.expires_at.strftime("%Y-%m-%d %H:%M:%S"))
        embed.add_field(name="Exception", value=error)
        embed.add_field(name="Item", value=item)
        output = utils.cut_string(str(vars(self)), 1900)
        output[0] = f'View object dump:\n{output[0]}'
        for message in output:
            await channel_out.send(f"```\n{message}```")
        await channel_out.send(embed=embed)
        self.log_error.send_output(traceback.format_exc(), channel_out)

        # remove interactions because of error
        self.clear_items()
        await self.message.edit(view=self)

