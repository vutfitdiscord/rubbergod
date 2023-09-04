"""
Cog implementing polls feature.

Description - Add a description to your poll
end_time - How long/until what time can people vote in this poll?
Max_votes - The maximum number of votes per user
Hide_Results - Hide the results of the poll until it has closed
voting_role - Require the member has a specific role to vote
Open_Poll - Allow people to add their own options to the poll
Image - Add an image to the poll
Anonymous - Hide who voted for what option
"""

from datetime import datetime, timedelta
from typing import Union

import disnake
from disnake.ext import commands

import utils
from buttons.poll import PollBooleanView
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.poll import PollDB, PollType


class Poll(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    def create_embed(
        self,
        title: str,
        description: str,
        author: Union[disnake.User, disnake.Member],
        end_datetime: datetime,
        poll_id: int,
        poll_options: list = [],
        max_votes: int = 1,
        image: str = None,
        anonymous: bool = False,
        **kwargs
    ):
        """Embed template for Vote"""
        end_datetime = utils.get_discord_timestamp(end_datetime, style="Relative Time")
        description = Messages.poll_embed_description(
            description=description,
            votes=max_votes,
            date=end_datetime,
            anonymous=anonymous,
            all_votes=0,
        )
        embed = disnake.Embed(
            title=title,
            description=description,
            color=disnake.Color.blue(),
        )
        for emoji, option in poll_options.items():
            embed.add_field(
                name=f"{emoji} {option}",
                value=f"{utils.create_bar(0, 0)} ({0} hlasů)",
                inline=False
            )
        embed.set_image(url=image)
        utils.add_author_footer(embed, author, additional_text=[f"ID: {poll_id}"])
        return embed

    @cooldowns.default_cooldown
    @commands.slash_command(name="poll")
    async def _poll(self, inter):
        pass

    @_poll.sub_command(name="boolean", description=Messages.poll_basic_brief)
    async def boolean(
        self,
        inter: disnake.ApplicationCommandInteraction,
        title: str = commands.Param(description=Messages.poll_boolean_title, max_length=256),
        description: str = commands.Param(
            default="",
            description=Messages.poll_boolean_description,
            max_length=3000
        ),
        endtime: str = commands.Param(default="1h", description=Messages.poll_boolean_endtime, max_length=40),
        image: disnake.Attachment = commands.Param(default=None, description=Messages.poll_boolean_image),
        anonymous: bool = commands.Param(default=False, description=Messages.poll_anonymous_vote),
    ):
        args = locals()
        args.pop("self")

        endtime = utils.parse_time(endtime, Messages.poll_boolean_endtime)
        now = inter.created_at.astimezone(
            tz=utils.get_local_zone()).replace(tzinfo=None) + timedelta(minutes=5)
        if endtime < now:
            await inter.send(Messages.poll_endtime_short, ephemeral=True)
            return

        args["author"] = inter.author
        args["author_id"] = inter.author.id
        args["image"] = image.url if image else None
        args["end_datetime"] = endtime
        args["poll_options"] = {"✅": "Ano", "❌": "Ne"}
        args["poll_type"] = PollType.boolean.value
        args["max_votes"] = 1
        args["message_url"] = ""

        poll = PollDB.add(**args)
        args["poll_id"] = poll.id

        embed = self.create_embed(**args)
        await inter.send(embed=embed, view=PollBooleanView(self.bot))
        message = await inter.original_message()

        poll.update_message_url(message_url=message.jump_url)
        if not anonymous:
            await message.create_thread(name=title[:100], auto_archive_duration=1440)


def setup(bot):
    bot.add_cog(Poll(bot))
