from typing import List

import disnake

import utils
from buttons.embed import PaginationView
from database.review import ReviewDB, ReviewRelevanceDB
from rubbergod import Rubbergod

from .features import ReviewManager
from .messages_cz import MessagesCZ


class ReviewView(PaginationView):
    def __init__(self, author: disnake.User, bot: Rubbergod, embeds: List[disnake.Embed], page: int = 1):
        super().__init__(author, embeds, row=1, end_arrow=False, timeout=300, page=page)
        self.bot = bot
        self.manager = ReviewManager(bot)

        self.up_button = disnake.ui.Button(emoji="🔼", style=disnake.ButtonStyle.primary, row=1)
        self.up_button.callback = self.up_callback

        self.down_button = disnake.ui.Button(emoji="🔽", style=disnake.ButtonStyle.primary, row=1)
        self.down_button.callback = self.down_callback

        self.check_review_text()
        if len(self.embed.fields) < 2:
            # if there aren't any reviews remove buttons
            self.clear_items()

    @property
    def review_id(self):
        return self.embed.footer.text.split("|")[-1][5:]

    @disnake.ui.button(emoji="👍", style=disnake.ButtonStyle.success, row=0)
    async def like(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_vote(interaction, True)

    @disnake.ui.button(emoji="🛑", style=disnake.ButtonStyle.grey, row=0)
    async def vote_remove(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_vote(interaction)

    @disnake.ui.button(emoji="👎", style=disnake.ButtonStyle.danger, row=0)
    async def dislike(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_vote(interaction, False)

    @disnake.ui.button(emoji="❔", style=disnake.ButtonStyle.primary, row=0)
    async def help(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.send(MessagesCZ.reviews_reaction_help, ephemeral=True)

    async def up_callback(self, interaction: disnake.MessageInteraction):
        await self.change_page_review(interaction, "prev")

    async def down_callback(self, interaction: disnake.MessageInteraction):
        await self.change_page_review(interaction, "next")

    async def pagination_callback(self, interaction: disnake.MessageInteraction, id: str):
        self.page = utils.embed.pagination_next(id, self.page, self.max_page, self.roll_around)
        self.check_review_text()
        await interaction.response.edit_message(embed=self.embed, view=self)

    def check_review_text(self) -> None:
        """Add or remove text pages buttons"""
        if len(self.embed.fields) > 3 and self.embed.fields[3].name == MessagesCZ.text_page_label:
            if self.up_button in self.children or self.down_button in self.children:
                return
            self.add_item(self.up_button)
            self.add_item(self.down_button)
        else:
            if self.up_button in self.children or self.down_button in self.children:
                # text pages are not present remove buttons
                self.remove_item(self.up_button)
                self.remove_item(self.down_button)

    async def change_page_review(self, interaction: disnake.MessageInteraction, page: str) -> None:
        review = ReviewDB.get_review_by_id(self.review_id)
        if not review:
            return

        pages = self.embed.fields[3].value.split("/")
        text_page = int(pages[0])
        max_text_page = int(pages[1])
        next_text_page = utils.embed.pagination_next(page, text_page, max_text_page)
        if next_text_page:
            self.embed = self.manager.update_embed(self.embed, review, next_text_page)
            await interaction.response.edit_message(embed=self.embed)

    async def handle_vote(self, interaction: disnake.MessageInteraction, vote: bool = None) -> None:
        review = ReviewDB.get_review_by_id(self.review_id)
        if not review:
            return

        member_id = str(interaction.author.id)
        if member_id == review.member_ID:
            await interaction.send(MessagesCZ.review_vote_own, ephemeral=True)
            return
        if vote is not None:
            self.manager.add_vote(self.review_id, vote, member_id)
        else:
            ReviewRelevanceDB.remove_vote(self.review_id, member_id)
        self.embed = self.manager.update_embed(self.embed, review)
        await interaction.response.edit_message(embed=self.embed)
