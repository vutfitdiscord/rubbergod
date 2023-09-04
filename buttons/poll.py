import asyncio
import re
from collections import deque
from typing import List, Optional

import disnake
from disnake.ext import commands, tasks

import utils
from buttons.base import BaseView
from config.messages import Messages
from database.poll import PollDB, PollOptionDB, VoterDB
from features.poll import extract_poll_id


class PollCache:
    def __init__(self, poll_list: list):
        self.cache = deque()

        if poll_list is not None:
            self.cache.extend(poll_list)

    def update_cache(self, poll_list: list) -> None:
        self.cache.clear()
        self.cache.extend(poll_list)

    def remove_item(self, item) -> None:
        try:
            self.cache.remove(item)
        except ValueError:
            pass

    def get_poll_by_id(self, id) -> Optional[PollDB]:
        for item in self.cache:
            if item.id == id:
                return item
        return None

    def get_cache(self) -> List[PollDB]:
        return list(self.cache)


class PollView(BaseView):
    def __init__(self):
        super().__init__(timeout=None)
        self.poll_cache = PollCache(PollDB.get_pending_polls())

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        poll_id = extract_poll_id(inter)
        poll = self.poll_cache.get_poll_by_id(poll_id)
        if poll is None:
            self.poll_cache.update_cache(PollDB.get_pending_polls())
            poll = self.poll_cache.get_poll_by_id(poll_id)

        if poll is None:
            poll = PollDB.get(poll_id)

        if poll.is_closed:
            self.poll_cache.remove_item(poll)
            await inter.message.edit(view=None)
            await inter.send(Messages.poll_closed(title=poll.title), ephemeral=True)
            return False

        # everything ok
        return True

    def update_embed(self, embed: disnake.Embed, poll: PollDB) -> disnake.Embed:
        embed.clear_fields()
        all_votes = poll.get_voters_count()
        for option in poll.options:
            votes = len(option.voters)
            embed.add_field(
                name=f"{option.emoji} {option.text}",
                value=f"{utils.create_bar(votes, all_votes)} ({votes} hlasů)",
                inline=False
            )

        pattern = r"- Celkový počet hlasů: (\d+)"
        embed.description = re.sub(pattern, f"- Celkový počet hlasů: {all_votes}", embed.description)

        return embed

    def check_duplicate_vote(
        self,
        inter: disnake.MessageInteraction,
        poll_option: PollOptionDB
    ) -> bool:
        """Check if user already voted in this option in current stack
        or in database and add to stack if not"""
        if str(inter.author.id) in poll_option.voters_ids:
            return True
        return False

    def get_poll(self, inter: disnake.MessageInteraction) -> Optional[PollDB]:
        poll_id = extract_poll_id(inter)
        poll = self.poll_cache.get_poll_by_id(poll_id)
        if poll is None:
            self.poll_cache.update_cache(PollDB.get_pending_polls())
            poll = self.poll_cache.get_poll_by_id(poll_id)
        return poll


class PollBooleanView(PollView):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.update_ids: set[tuple] = set()
        self.lock = asyncio.Lock()
        self.process_interactions.start()

    @tasks.loop(seconds=10.0)
    async def process_interactions(self):
        async with self.lock:
            update_ids = self.update_ids.copy()
            self.update_ids.clear()

        for poll, message in update_ids:
            embed = self.update_embed(message.embeds[0], poll)
            await message.edit(embed=embed)

    @disnake.ui.button(
        label="Ano",
        emoji="✅",
        style=disnake.ButtonStyle.primary,
        custom_id="poll:boolean:yes"
    )
    async def boolean_yes(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()

        poll = self.get_poll(inter)

        # find poll option matching label
        poll_option = next((option for option in poll.options if option.text == button.label), None)

        vote_check = self.check_duplicate_vote(inter, poll_option)

        if vote_check:
            await inter.send(
                Messages.poll_already_voted(option=f"{button.emoji} {button.label}"),
                ephemeral=True,
                view=PollRemoveVoteView(self, poll, poll_option)
            )
            return

        # add user to voters
        if poll_option:
            self.update_ids.add((poll, inter.message))
            poll_option.add_voter(inter.user.id)

        await inter.send(
            Messages.poll_voted(option=f"{button.emoji} {button.label}"),
            ephemeral=True,
            view=PollRemoveVoteView(self, poll, poll_option)
        )

    @disnake.ui.button(
        label="Ne",
        emoji="❌",
        style=disnake.ButtonStyle.primary,
        custom_id="poll:boolean:no"
    )
    async def boolean_no(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()

        poll = self.get_poll(inter)

        # find poll option matching label
        poll_option = next((option for option in poll.options if option.text == button.label), None)

        vote_check = self.check_duplicate_vote(inter, poll_option)

        if vote_check:
            await inter.send(
                Messages.poll_already_voted(option=f"{button.emoji} {button.label}"),
                ephemeral=True,
                view=PollRemoveVoteView(self, poll, poll_option)
            )
            return

        # add user to voters
        if poll_option:
            self.update_ids.add((poll, inter.message))
            poll_option.add_voter(inter.user.id)

        await inter.send(
            Messages.poll_voted(option=f"{button.emoji} {button.label}"),
            ephemeral=True,
            view=PollRemoveVoteView(self, poll, poll_option)
        )


class PollRemoveVoteView(BaseView):
    def __init__(self, instance_parent: PollBooleanView, poll: PollDB, poll_option: PollOptionDB):
        super().__init__()
        self.update_ids: set[tuple] = instance_parent.update_ids
        self.poll = poll
        self.poll_option = poll_option

    @disnake.ui.button(
        label="Odstranit hlas",
        emoji="🗑️",
        style=disnake.ButtonStyle.danger,
        custom_id="poll:remove:vote"
    )
    async def remove_vote(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()

        voter = VoterDB.get(inter.user.id)
        self.poll_option.remove_voter(voter)

        try:
            message: disnake.Message = await commands.MessageConverter().convert(inter, self.poll.message_url)
        except commands.MessageNotFound:
            await inter.send(Messages.message_not_found, ephemeral=True)
            return

        self.update_ids.add((self.poll, message))
        await inter.edit_original_message(Messages.poll_vote_removed(title=self.poll.title), view=None)

    @disnake.ui.button(
        label="Odstranit všechny moje hlasy",
        emoji="🗑️",
        style=disnake.ButtonStyle.danger,
        custom_id="poll:remove:votes"
    )
    async def remove_votes(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await inter.response.defer()

        voter = VoterDB.get(inter.user.id)
        self.poll.remove_voter(voter)

        try:
            message: disnake.Message = await commands.MessageConverter().convert(inter, self.poll.message_url)
        except commands.MessageNotFound:
            await inter.send(Messages.message_not_found, ephemeral=True)
            return

        self.update_ids.add((self.poll, message))
        await inter.edit_original_message(Messages.poll_vote_removed(title=self.poll.title), view=None)
