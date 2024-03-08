"""
Cog implementing polls feature.

Title - Title/Question of the poll
Description - Add a description to your poll
end_time - How long/until what time can people vote in this poll?
Max_votes - The maximum number of votes per user
Open_Poll - Allow people to add their own options to the poll
Image or Attachment - Add an image or attachment to the poll
Anonymous - Hide who voted for what option
"""

from datetime import datetime, timezone

import disnake
from disnake.ext import commands, tasks

import utils
from buttons.general import TrashView
from buttons.poll import (PollBooleanView, PollOpinionView, PollView,
                          PollVotersView)
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.poll import PollDB, PollType
from features import poll as poll_features
from permissions.room_check import RoomCheck

time_choices = ["1y 1M 1w 1d 1h 1m 1s", "DD.MM.YYYY HH:MM", "DD.MM.YYYY", "HH:MM", "Never"]


class Poll(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.check = RoomCheck(bot)

    async def poll_create(self, args: dict, poll_options: dict, poll_view: disnake.ui.View):
        inter = args.get("inter")
        attachment = args.get("attachment")
        anonymous = args.get("anonymous")
        endtime = args.get("endtime")

        endtime_check, endtime = poll_features.check_endtime(inter, endtime)
        if endtime_check:
            await inter.send(Messages.poll_endtime_short, ephemeral=True)
            return

        if attachment and attachment.size > 25000000:       # 25MB
            await inter.send(Messages.attachment_too_big, ephemeral=True)
            return

        type, attachment = await poll_features.parse_attachment(attachment)
        file = [attachment] if type == "file" else []

        args["author"] = inter.author
        args["author_id"] = inter.author.id
        args["image"] = attachment if type == "image" else None
        args["end_datetime"] = endtime
        args["poll_options"] = poll_options
        args["poll_type"] = PollType.boolean.value
        args["max_votes"] = 1
        args["message_url"] = ""

        poll = PollDB.add(**args)
        args["poll_id"] = poll.id

        embed = poll_features.create_embed(**args)

        if anonymous:
            await inter.send(embed=embed, view=poll_view, files=file)
        else:
            voters_view = PollVotersView(self.bot)
            poll_view.children.extend(voters_view.children)
            await inter.send(embed=embed, view=poll_view, files=file)

        message = await inter.original_message()
        poll.update_message_url(message_url=message.jump_url)
        self.task_generator(poll)

    @commands.slash_command(name="poll")
    async def _poll(self, inter: disnake.GuildCommandInteraction): ...

    # TODO
    # @cooldowns.long_cooldown
    # @_poll.sub_command(name="basic", description=Messages.poll_basic_brief)
    # async def basic(
    #     self,
    #     inter: disnake.ApplicationCommandInteraction,
    #     title: str = commands.Param(description=Messages.poll_title, max_length=256),
    #     description: str = commands.Param(
    #         default="",
    #         description=Messages.poll_description,
    #         max_length=3000
    #     ),
    #     endtime: str = commands.Param(
    #         default="1h",
    #         description=Messages.poll_endtime,
    #         max_length=40,
    #         autocomplete=time_choices
    #     ),
    #     attachment: disnake.Attachment = commands.Param(
    #         default=None, description=Messages.poll_attachment
    #     ),
    #     anonymous: bool = commands.Param(default=False, description=Messages.poll_anonymous_vote),
    #     max_votes: int = 1,
    #     # open_poll: bool = False,
    # ):
    #     await inter.response.defer()
    #     await inter.send("asdf", view=PollBasicView(self.bot))

    @cooldowns.long_cooldown
    @_poll.sub_command(name="boolean", description=Messages.poll_boolean_brief)
    async def boolean(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str = commands.Param(description=Messages.poll_title, max_length=256),
        description: str = commands.Param(
            default="",
            description=Messages.poll_description,
            max_length=3000
        ),
        endtime: str = commands.Param(
            default="1h",
            description=Messages.time_format,
            max_length=40,
            autocomplete=time_choices
        ),
        attachment: disnake.Attachment = commands.Param(
            default=None, description=Messages.poll_attachment
        ),
        anonymous: bool = commands.Param(default=False, description=Messages.poll_anonymous_vote),
    ):
        await inter.response.defer()
        args = locals()
        args.pop("self")

        await self.poll_create(
            args,
            poll_options={"✅": "Ano", "❌": "Ne"},
            poll_view=PollBooleanView(self.bot)
        )

    @cooldowns.long_cooldown
    @_poll.sub_command(name="opinion", description=Messages.poll_opinion_brief)
    async def opinion(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str = commands.Param(description=Messages.poll_title, max_length=256),
        description: str = commands.Param(
            default="",
            description=Messages.poll_description,
            max_length=3000
        ),
        endtime: str = commands.Param(
            default="1h",
            description=Messages.time_format,
            max_length=40,
            autocomplete=time_choices
        ),
        attachment: disnake.Attachment = commands.Param(
            default=None, description=Messages.poll_attachment
        ),
        anonymous: bool = commands.Param(default=False, description=Messages.poll_anonymous_vote),
    ):
        await inter.response.defer()
        args = locals()
        args.pop("self")

        await self.poll_create(
            args,
            poll_options={"✅": "Souhlasím", "😐": "Neutral", "❌": "Nesouhlasím"},
            poll_view=PollOpinionView(self.bot)
        )

    @cooldowns.default_cooldown
    @_poll.sub_command(name="list", description=Messages.poll_list_brief)
    async def list_polls(
        self,
        inter: disnake.ApplicationCommandInteraction,
        poll_type: str = commands.Param(
            default=None,
            choices=[PollType.basic.name, PollType.boolean.name, PollType.opinion.name])
    ):
        await inter.response.defer(ephemeral=True)
        if not poll_type:
            header = "# Aktivní hlasování:\n"
            polls = PollDB.get_pending_polls()
        else:
            header = f"# {poll_type.capitalize()} aktivní hlasování:\n"
            polls = PollDB.get_pending_polls_by_type(PollType[poll_type].value)

        if not polls:
            await inter.send(Messages.poll_no_active_polls)
            return

        content = ""
        for poll in polls:
            message = await utils.get_message_from_url(self.bot, poll.message_url)
            if not message or not message.embeds:
                # If the poll is not found, delete the poll
                poll.remove()
                continue

            permission = message.channel.permissions_for(inter.author)
            if permission.view_channel:
                content += Messages.poll_list_polls(id=poll.id, url=poll.message_url, title=poll.title)

        if not content:
            await inter.send(Messages.poll_no_active_polls)
            return

        content = utils.cut_string_by_words(header + content, 1900, "\n")
        for content_part in content:
            await inter.send(content_part, ephemeral=True)

    async def task_end_poll(self, poll: PollDB) -> None:
        """Ends the poll"""
        if poll.closed:
            return

        message = await utils.get_message_from_url(self.bot, poll.message_url)
        author = await self.bot.get_or_fetch_user(poll.author_id)
        await PollView.action_cache.end_poll(poll.id)

        if not message or not message.embeds:
            poll.remove()
            return

        poll_view = None
        authors_view = TrashView(row=1)
        if not poll.anonymous:
            poll_view = PollVotersView(self.bot)
            authors_view.children.extend(poll_view.children)
        await message.edit(view=poll_view)

        if author is not None:
            content = poll_features.create_end_poll_message(poll)
            embed = message.embeds[0]
            await author.send(content=content, embed=embed, view=authors_view)
            await message.channel.send(content=content, embed=embed, view=poll_view)

    def task_generator(self, poll: PollDB) -> None:
        """Generator for tasks to close polls"""
        current_time = datetime.now(timezone.utc)
        end_time = poll.end_datetime.time()
        target_datetime = datetime.combine(current_time.date(), end_time)
        time_until = (target_datetime - current_time).total_seconds()

        if time_until < 0:
            return

        def wrapper():
            self.bot.loop.create_task(self.task_end_poll(poll))

        task = self.bot.loop.call_later(time_until, wrapper)

        self.tasks.append(task)
        PollView.tasks[poll.id] = task

    def cog_load(self) -> None:
        """Generate tasks on cog load to close active polls"""
        polls = PollDB.get_pending_polls()
        for poll in polls:
            self.task_generator(poll)

        self.tasks = [PollTask().process_interactions.start()]


class PollTask(PollView):
    """Class only for having task loop"""
    def __init__(self):
        super().__init__()

    @tasks.loop(seconds=10.0)
    async def process_interactions(self):
        update_ids = await self.action_cache.apply_cache()
        for poll_id in update_ids:
            poll = PollDB.get(poll_id)
            message = self.messages.get(poll_id, None)

            if not message:
                continue

            if poll.closed:
                embed = poll_features.close_embed(message.embeds[0], poll, poll.closed_by, poll.end_datetime)
                await message.edit(embed=embed, attachments=None)
                continue

            embed = poll_features.update_embed(message.embeds[0], poll)
            await message.edit(embed=embed, attachments=None)


def setup(bot):
    bot.add_cog(Poll(bot))
