import asyncio
from datetime import datetime, timezone

import disnake
from disnake.ext import commands

import utils
from buttons.base import BaseView
from buttons.general import TrashView
from config.messages import Messages
from database.poll import PollDB, PollOptionDB
from features import poll as poll_features


class Action:
    def __init__(self, action: str, value: int | list[int] = None):
        self.action = action
        self.value = value


class ActionsCache:
    def __init__(self) -> None:
        # {poll_id: {voter_id: Action}}
        self.memory: dict[int, dict[int, Action]] = {}
        self.lock = asyncio.Lock()

    async def add_vote(self, poll_id: int, voter_id: str, poll_option_id: int) -> None:
        async with self.lock:
            if not self.memory.get(poll_id):
                self.memory[poll_id] = {}
            self.memory[poll_id][voter_id] = Action("add", poll_option_id)

    async def add_multiple_choice(self, poll_id: int, voter_id: str, poll_option_ids: list[int]) -> None:
        async with self.lock:
            if not self.memory.get(poll_id):
                self.memory[poll_id] = {}
            self.memory[poll_id][voter_id] = Action("add_multiple", poll_option_ids)

    async def remove_vote(self, poll_id: int, voter_id: str, poll_option_id: int) -> None:
        """Remove vote from user on poll option in db"""
        async with self.lock:
            if not self.memory.get(poll_id):
                self.memory[poll_id] = {}
            self.memory[poll_id][voter_id] = Action("remove", poll_option_id)

    async def remove_voter_from_cache(self, poll_id: int, voter_id: str) -> None:
        """Remove voter only from cache"""
        async with self.lock:
            poll_dict = self.memory.get(poll_id)
            if poll_dict and voter_id in poll_dict:
                poll_dict.pop(voter_id, None)

    async def voter_in_cache(self, poll_id: int, voter_id: str) -> bool:
        async with self.lock:
            poll_dict = self.memory.get(poll_id)
            if poll_dict and voter_id in poll_dict:
                return True
            return False

    def process_actions(self, poll_id: int, users_actions: dict) -> None:
        for user_id, action in users_actions.items():
            try:
                if action.action == "add":
                    PollDB.get(poll_id).add_voter(user_id, action.value)

                elif action.action == "add_multiple":
                    # TODO - add multiple choice function in db
                    pass

                elif action.action == "remove":
                    PollDB.get(poll_id).remove_voter(user_id)

            except AttributeError:
                pass

    async def apply_cache(self) -> set[int]:
        async with self.lock:
            memory_copy = self.memory.copy()

        for poll_id, users_actions in memory_copy.items():
            self.process_actions(poll_id, users_actions)

        async with self.lock:
            self.memory = {}

        return set(memory_copy.keys())

    async def end_poll(self, poll_id: int) -> None:
        """End poll finish all actions in cache for it"""
        async with self.lock:
            memory_copy = self.memory.copy()

        poll_cache = memory_copy.get(poll_id)
        if not poll_cache:
            return
        self.process_actions(poll_id, poll_cache)
        async with self.lock:
            self.memory.pop(poll_id, None)


class PollView(BaseView):
    action_cache = ActionsCache()
    messages: dict[int, disnake.Message] = {}
    tasks = {}

    def __init__(self):
        super().__init__(timeout=None)
        self.button_cd = commands.CooldownMapping.from_cooldown(4, 10.0, commands.BucketType.user)

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        if await poll_features.has_cooldown(inter, self.button_cd):
            return False

        if not inter.message.embeds:
            await inter.message.delete()
            return False

        await inter.response.defer()
        if inter.data.custom_id == "poll:voters":
            # voters are always available
            return True

        poll_id = poll_features.extract_poll_id(inter.message)
        poll = PollDB.get(poll_id)

        if not poll.is_active:
            # poll ended or closed
            content = poll_features.create_end_poll_message(poll)
            await inter.message.edit(view=None)
            await inter.send(content=content, ephemeral=True)
            return False

        # everything ok
        return True

    async def button_action(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        poll_id = poll_features.extract_poll_id(inter.message)
        poll = PollDB.get(poll_id)

        # find poll option matching label
        poll_option = next((option for option in poll.options if option.text == button.label), None)

        if str(inter.author.id) in poll_option.voters_ids:
            await inter.send(
                Messages.poll_already_voted(option=f"{button.emoji} {button.label}"),
                ephemeral=True,
                view=PollRemoveVoteView(self, poll, poll_option),
            )
            return

        await self.action_cache.add_vote(poll_id, str(inter.author.id), poll_option.id)
        self.messages[poll_id] = inter.message

        await inter.send(
            Messages.poll_voted(option=f"{button.emoji} {button.label}"),
            ephemeral=True,
            view=PollRemoveVoteView(self, poll, poll_option),
        )


class PollBasicView(PollView):  # TODO
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot


class PollBooleanView(PollView):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.children.extend(PollCloseView(bot).children)

    @disnake.ui.button(
        label="Ano", emoji="✅", style=disnake.ButtonStyle.primary, custom_id="poll:boolean:yes"
    )
    async def boolean_yes(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await self.button_action(button, inter)

    @disnake.ui.button(label="Ne", emoji="❌", style=disnake.ButtonStyle.primary, custom_id="poll:boolean:no")
    async def boolean_no(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await self.button_action(button, inter)


class PollOpinionView(PollView):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.children.extend(PollCloseView(bot).children)

    @disnake.ui.button(
        label="Souhlasím", emoji="✅", style=disnake.ButtonStyle.primary, custom_id="poll:opinion:agree"
    )
    async def opinion_agree(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await self.button_action(button, inter)

    @disnake.ui.button(
        label="Neutral", emoji="😐", style=disnake.ButtonStyle.primary, custom_id="poll:opinion:neutral"
    )
    async def opinion_neutral(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await self.button_action(button, inter)

    @disnake.ui.button(
        label="Nesouhlasím", emoji="❌", style=disnake.ButtonStyle.primary, custom_id="poll:opinion:disagree"
    )
    async def opinion_disagree(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await self.button_action(button, inter)


class PollRemoveVoteView(PollView):
    def __init__(self, instance_parent: PollBooleanView, poll: PollDB, poll_option: PollOptionDB):
        super().__init__()
        self.action_cache = instance_parent.action_cache
        self.messages = instance_parent.messages
        self.bot = instance_parent.bot
        self.poll = poll
        self.poll_option = poll_option

    async def interaction_check(self, inter: disnake.Interaction) -> bool:
        await inter.response.defer()
        return True

    async def button_action(
        self, action: str, button: disnake.ui.Button, inter: disnake.MessageInteraction
    ) -> None:
        message = self.messages.get(self.poll.id)
        if not message:
            message: disnake.Message = await utils.get_message_from_url(self.bot, self.poll.message_url)
            if not message:
                # poll message not found
                await inter.edit_original_message(Messages.message_not_found)
                return
            self.messages[self.poll.id] = message

        poll = PollDB.get(self.poll.id)
        if not poll:
            await inter.edit_original_message(Messages.poll_not_found, view=None)
            return

        if not poll.is_active:
            content = poll_features.create_end_poll_message(poll)
            await inter.edit_original_message(content=content, view=None)
            return

        if not poll.has_voted(inter.author.id) and not await self.action_cache.voter_in_cache(
            poll.id, str(inter.user.id)
        ):
            # user wants to remove his vote but there is no vote to remove
            await inter.edit_original_message(Messages.poll_not_voted, view=None)
            return

        await self.action_cache.remove_voter_from_cache(poll.id, str(inter.user.id))
        await self.action_cache.remove_vote(poll.id, str(inter.user.id), self.poll_option.id)
        await inter.edit_original_message(
            Messages.poll_vote_removed(title=self.poll.title, url=message.jump_url), view=None
        )

        # TODO - raise error

    @disnake.ui.button(
        label="Odstranit hlas", emoji="🗑️", style=disnake.ButtonStyle.danger, custom_id="poll:remove:vote"
    )
    async def remove_vote(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        await self.button_action("remove_vote", button, inter)

    # @disnake.ui.button(
    #     label="Odstranit všechny moje hlasy",
    #     emoji="🗑️",
    #     style=disnake.ButtonStyle.danger,
    #     custom_id="poll:remove:votes"
    # )
    # async def remove_votes(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
    #     await self.button_action("remove_votes", button, inter)


class PollVotersView(PollView):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @disnake.ui.button(
        label="Zobrazit hlasy", emoji="🗒️", style=disnake.ButtonStyle.grey, custom_id="poll:voters", row=1
    )
    async def boolean_voters(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        content = await poll_features.list_voters(inter)
        for content_part in content:
            await inter.send(content_part, ephemeral=True)


class PollCloseView(PollView):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @disnake.ui.button(
        label="Ukončit hlasování", emoji="🔒", style=disnake.ButtonStyle.grey, custom_id="poll:close", row=1
    )
    async def poll_close(self, button: disnake.ui.Button, inter: disnake.MessageInteraction) -> None:
        poll_id = poll_features.extract_poll_id(inter.message)
        author_id = PollDB.get_author_id(poll_id)
        if author_id != str(inter.author.id):
            await inter.send(Messages.poll_not_author, ephemeral=True)
            return

        await self.action_cache.end_poll(poll_id)
        self.tasks[poll_id].cancel()

        poll = PollDB.get(poll_id)
        now = datetime.now()
        author = await self.bot.get_or_fetch_user(poll.author_id)
        poll.update_closed(True, inter.author.id, datetime.now(timezone.utc))
        embed = poll_features.close_embed(inter.message.embeds[0], poll, inter.author.id, now)
        poll_view = None
        author_view = TrashView(row=1)
        if not poll.anonymous:
            poll_view = PollVotersView(self.bot)
            author_view.children.extend(poll_view.children)

        content = poll_features.create_end_poll_message(poll)
        await inter.message.edit(content=content, embed=embed, view=poll_view, attachments=None)
        try:
            await author.send(content=content, embed=embed, view=author_view)
        except disnake.Forbidden:
            pass
        await inter.message.reply(content=content, embed=embed, view=poll_view)


class PollModal(disnake.ui.Modal):  # TODO
    def __init__(self, view, bot, inter: disnake.MessageInteraction, report_id: int) -> None:
        self.view = view
        self.bot = bot
        self.inter = inter
        self.report_id = report_id
        self.title = Messages.report_answer_title(id=report_id)
        components = [
            disnake.ui.TextInput(
                label=self.title,
                placeholder=Messages.report_answer,
                custom_id="answer",
                style=disnake.TextInputStyle.long,
                required=True,
                max_length=2000,
            )
        ]

        super().__init__(title=self.title, custom_id="poll_modal", timeout=900, components=components)

    async def callback(self, inter: disnake.ModalInteraction) -> None: ...
