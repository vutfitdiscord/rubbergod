import disnake
from typing import Callable, List

from config.messages import Messages
import utils


class EmbedView(disnake.ui.View):

    def __init__(
        self,
        embeds: List[disnake.Embed],
        row: int = 1,
        author: int = 0,
        roll_arroud: bool = True,
        end_arrow: bool = True,
        callback: Callable = None,
        timeout: int = 300
    ):
        """Embed pagination view

        param: List[disnake.Embed] embeds: List of embed to be paginated
        param int row: On which row should be buttons added, defaults to first
        param int author: If presented allow just message autor to change pages
        param bool roll_arroud: After last page rollaround to first
        param bool end_arrow: If true use also '⏩' button
        param Callable callback(page, embed): Use when there are a lot of embeds,
            embeds should contain one embed, page number and embed are passed as parameters
        param int timeout: Seconds until disabling interaction, use None for always enabled
        """
        self.page = 1
        self.callback = callback
        self.roll_arroud = roll_arroud
        self.author = author
        self.max_page = 1000
        if self.callback is None:
            self.max_page = len(embeds)
        else:
            end_arrow = False
        self.embeds = embeds
        super().__init__(timeout=timeout)
        if self.max_page <= 1:
            return
        self.add_item(
            disnake.ui.Button(
                emoji="⏪",
                custom_id="embed:start_page",
                row=row,
                style=disnake.ButtonStyle.primary
            )
        )
        self.add_item(
            disnake.ui.Button(
                emoji="◀",
                custom_id="embed:prev_page",
                row=row,
                style=disnake.ButtonStyle.primary
            )
        )
        self.add_item(
            disnake.ui.Button(
                emoji="▶",
                custom_id="embed:next_page",
                row=row,
                style=disnake.ButtonStyle.primary
            )
        )
        if end_arrow:
            self.add_item(
                disnake.ui.Button(
                    emoji="⏩",
                    custom_id="embed:end_page",
                    row=row,
                    style=disnake.ButtonStyle.primary
                )
            )

    @property
    def embed(self):
        if self.callback is None:
            return self.embeds[self.page-1]
        else:
            return self.callback(self.page, self.embeds[0])

    @embed.setter
    def embed(self, value):
        self.embeds[self.page-1] = value

    async def interaction_check(self, interaction: disnake.Interaction) -> None:
        ids = ["embed:start_page", "embed:prev_page", "embed:next_page", "embed:end_page"]
        if interaction.data.custom_id not in ids or self.max_page <= 1:
            return
        if self.author and interaction.author.id != self.author:
            await interaction.send(Messages.embed_not_author, ephemeral=True)
            return
        self.page = utils.pagination_next(
            interaction.data.custom_id,
            self.page,
            self.max_page,
            self.roll_arroud
        )
        await interaction.response.edit_message(embed=self.embed)
