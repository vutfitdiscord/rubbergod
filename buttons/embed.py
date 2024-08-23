import disnake

import utils
from buttons.base import BaseView
from config.messages import Messages
from features.leaderboard import LeaderboardPageSource


class PaginationView(BaseView):
    message: disnake.Message

    def __init__(
        self,
        author: disnake.User,
        embeds: list[disnake.Embed],
        row: int = 0,
        perma_lock: bool = False,
        roll_around: bool = True,
        end_arrow: bool = True,
        page_source: LeaderboardPageSource = None,
        timeout: int = 300,
        page: int = 1,
        show_page: bool = False,
    ):
        """Embed pagination view

        :param disnake.User author: command author, used for locking pagination.
        :param List[disnake.Embed] embeds: List of embeds to be paginated.
        :param int row: On which row should the buttons be added, defaults to the first row.
        :param bool perma_lock: If True, only the message author can change pages without the dynamic lock button.
        :param bool roll_around: If True, after reaching the last page, roll around to the first page.
        :param bool end_arrow: If True, use the '⏩' button as well.
        :param LeaderboardPageSource page_source: Used for long leaderboards, where embeds should contain one embed.
        :param int timeout: Seconds until disabling interaction, use None for always enabled.
        :param int page: Starting page.
        :param bool show_page: Show the page number at the bottom of the embed, e.g.: 2/4.
        """
        super().__init__(timeout=timeout)
        self.author = author
        self.embeds = embeds
        self.row = row
        self.perma_lock = perma_lock
        self.roll_around = roll_around
        self.page_source = page_source
        self.page = page
        self.dynam_lock = False

        if not self.page_source:
            self.max_page = len(embeds)
        else:
            self.max_page = self.page_source.get_max_pages()
            end_arrow = False

        if self.max_page <= 1:
            return  # No need for pagination

        if show_page:
            self.add_page_numbers()

        # Add all buttons to the view and set their callbacks
        self.start_button = disnake.ui.Button(emoji="⏪", row=row, style=disnake.ButtonStyle.primary)
        self.start_button.callback = self.start_callback
        self.add_item(self.start_button)

        self.prev_button = disnake.ui.Button(emoji="◀", row=row, style=disnake.ButtonStyle.primary)
        self.prev_button.callback = self.prev_callback
        self.add_item(self.prev_button)

        self.next_button = disnake.ui.Button(emoji="▶", row=row, style=disnake.ButtonStyle.primary)
        self.next_button.callback = self.next_callback
        self.add_item(self.next_button)

        if end_arrow:
            self.end_button = disnake.ui.Button(emoji="⏩", row=row, style=disnake.ButtonStyle.primary)
            self.end_button.callback = self.end_callback
            self.add_item(self.end_button)

        if not self.perma_lock:
            # if permanent lock is not applied, dynamic lock is added
            self.lock_button = disnake.ui.Button(emoji="🔓", row=0, style=disnake.ButtonStyle.success)
            self.lock_button.callback = self.lock_callback
            self.add_item(self.lock_button)

    @property
    def embed(self):
        if self.page_source is None:
            return self.embeds[self.page - 1]
        else:
            page = self.page_source.get_page(self.page - 1)
            return self.page_source.format_page(page)

    @embed.setter
    def embed(self, value):
        self.embeds[self.page - 1] = value

    def add_page_numbers(self):
        """Set footers with page numbers for each embed in list"""
        for page, embed in enumerate(self.embeds):
            utils.embed.add_author_footer(
                embed, self.author, additional_text=[f"Page {page+1}/{self.max_page}"]
            )

    async def lock_callback(self, interaction: disnake.MessageInteraction):
        self.dynam_lock = not self.dynam_lock
        if self.dynam_lock:
            self.lock_button.style = disnake.ButtonStyle.danger
            self.lock_button.emoji = "🔒"
        else:
            self.lock_button.style = disnake.ButtonStyle.success
            self.lock_button.emoji = "🔓"
        await interaction.response.edit_message(view=self)

    async def start_callback(self, interaction: disnake.MessageInteraction):
        await self.pagination_callback(interaction, "start")

    async def prev_callback(self, interaction: disnake.MessageInteraction):
        await self.pagination_callback(interaction, "prev")

    async def next_callback(self, interaction: disnake.MessageInteraction):
        await self.pagination_callback(interaction, "next")

    async def end_callback(self, interaction: disnake.MessageInteraction):
        await self.pagination_callback(interaction, "end")

    async def pagination_callback(self, interaction: disnake.MessageInteraction, id: str):
        self.page = utils.embed.pagination_next(id, self.page, self.max_page, self.roll_around)
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> bool:
        if (self.perma_lock or self.dynam_lock) and interaction.author.id != self.author.id:
            """Message has permanent lock or dynamic lock enabled"""
            await interaction.send(Messages.embed_not_author, ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        await self.message.edit(view=None)
