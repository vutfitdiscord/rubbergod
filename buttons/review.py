from typing import List

import disnake

import utils
from buttons.embed import EmbedView, ViewRowFull
from config.messages import Messages
from database.review import ReviewDB, ReviewRelevanceDB
from features.review import ReviewManager


class ReviewView(EmbedView):

    def __init__(self, author: disnake.User, bot: disnake.Client, embeds: List[disnake.Embed], page: int = 1):
        self.bot = bot
        self.manager = ReviewManager(bot)
        self.total_pages = len(embeds)
        super().__init__(author, embeds, row=1, end_arrow=False, timeout=300, page=page)
        self.check_text_pages()
        # if there aren't any reviews remove buttons
        if len(self.embed.fields) < 2:
            for child in self.children:
                child.disabled = True

    def check_text_pages(self):
        if (
            len(self.embed.fields) > 3
            and self.embed.fields[3].name == Messages.review_text_page_label
        ):
            self.add_item(
                disnake.ui.Button(
                    emoji="🔽",
                    custom_id="review:next_text",
                    style=disnake.ButtonStyle.primary,
                    row=1
                )
            )
            self.add_item(
                disnake.ui.Button(
                    emoji="🔼",
                    custom_id="review:prev_text",
                    style=disnake.ButtonStyle.primary,
                    row=1
                )
            )
        else:
            for child in self.children:
                if "text" in child.custom_id:
                    child.disabled = True

    @property
    def review_id(self):
        return self.embed.footer.text.split("|")[-1][5:]

    async def handle_vote(self, interaction: disnake.MessageInteraction, vote: bool = None):
        review = ReviewDB.get_review_by_id(self.review_id)
        if review:
            member_id = str(interaction.author.id)
            if member_id == review.member_ID:
                await interaction.send(Messages.review_vote_own, ephemeral=True)
                return
            if vote is not None:
                self.manager.add_vote(self.review_id, vote, member_id)
            else:
                ReviewRelevanceDB.remove_vote(self.review_id, member_id)
            self.embed = self.manager.update_embed(self.embed, review)
            await interaction.response.edit_message(embed=self.embed)

    @disnake.ui.button(emoji="👍", custom_id="review:like", style=disnake.ButtonStyle.success, row=0)
    async def like(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_vote(interaction, True)

    @disnake.ui.button(emoji="🛑", custom_id="review:vote_remove", row=0)
    async def vote_remove(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_vote(interaction)

    @disnake.ui.button(emoji="👎", custom_id="review:dislike", style=disnake.ButtonStyle.danger, row=0)
    async def dislike(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await self.handle_vote(interaction, False)

    @disnake.ui.button(emoji="❔", custom_id="review:help", style=disnake.ButtonStyle.primary, row=0)
    async def help(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
        await interaction.send(Messages.reviews_reaction_help, ephemeral=True)

    async def interaction_check(self, interaction: disnake.MessageInteraction) -> None:
        if interaction.data.custom_id == "embed:lock":
            await super().interaction_check(interaction)
            return False
        elif "review" not in interaction.data.custom_id:
            # pagination interaction from super class
            if await super().interaction_check(interaction) is not False:
                # pagination has changed the page
                try:
                    self.check_text_pages()
                    view = self
                except ViewRowFull:
                    # there was an issue while adding buttons; recreate view
                    view = ReviewView(self.author, self.bot, self.embeds, page=self.page)
                    # set the page of new view to the current one
                # update view
                await interaction.edit_original_response(view=view)
            return False
        elif (
            "text" in interaction.data.custom_id and
            self.embed.fields[3].name == Messages.review_text_page_label
        ):
            if (self.perma_lock or self.locked) and interaction.author.id != self.author.id:
                await interaction.send(Messages.embed_not_author, ephemeral=True)
                return False
            # text page pagination
            review = ReviewDB.get_review_by_id(self.review_id)
            if review:
                pages = self.embed.fields[3].value.split("/")
                text_page = int(pages[0])
                max_text_page = int(pages[1])
                next_text_page = utils.pagination_next(interaction.data.custom_id, text_page, max_text_page)
                if next_text_page:
                    self.embed = self.manager.update_embed(self.embed, review, next_text_page)
                    await interaction.response.edit_message(embed=self.embed)
            return False
        # fallback to buttons callbacks
        return True
