"""
Cog for handling vote reactions for contests.
"""
from __future__ import annotations

from functools import cached_property

import disnake
from disnake.ext import commands

import utils
from buttons.contestvote import ContestView
from buttons.general import TrashView
from cogs.base import Base
from config import cooldowns
from config.messages import Messages
from database.contestvote import ContestVoteDB
from features.contestvote import get_top_contributions
from features.reaction_context import ReactionContext
from modals.contestvote import DenyContributionModal
from permissions.permission_check import submod_plus
from permissions.room_check import RoomCheck


class ContestVote(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.check = RoomCheck(bot)

        self.emojis = {
            str('1️⃣'): self.config.contest_vote_weight_1,
            str('2️⃣'): self.config.contest_vote_weight_2,
            str('3️⃣'): self.config.contest_vote_weight_3
        }

    @cached_property
    def filter_channel(self) -> disnake.TextChannel:
        return self.bot.get_channel(self.config.contest_vote_filter_channel)

    @cached_property
    def contest_vote_channel(self) -> disnake.TextChannel:
        return self.bot.get_channel(self.config.contest_vote_channel)

    @commands.slash_command(name='contest',)
    async def contest(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @cooldowns.default_cooldown
    @contest.sub_command(
        name='calculate_contribution',
        description=Messages.contest_vote_calculate_contribution_brief
    )
    async def calculate_contribution(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message_url: disnake.Message
    ):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))

        if message_url.channel != self.contest_vote_channel:
            await inter.send(Messages.contest_vote_not_contest_channel)
            return

        if not message_url.reactions:
            await inter.send(Messages.contest_vote_no_reactions)
            return

        contributions = await get_top_contributions(self, [message_url], 1)

        await inter.send(''.join(contributions))

    @commands.cooldown(rate=1, per=600.0, type=commands.BucketType.user)
    @contest.sub_command(
        name='top_contributions',
        description=Messages.contest_vote_top_contributions_brief,
    )
    async def top_contributions(
        self,
        inter: disnake.ApplicationCommandInteraction,
        number_of: int = commands.Param(
            default=5, gt=0, le=10, description=Messages.contest_vote_number_of_param
        )
    ):
        await inter.response.defer(ephemeral=self.check.botroom_check(inter))
        messages = await self.contest_vote_channel.history().flatten()

        contributions = await get_top_contributions(self, messages, number_of)

        if not contributions:
            await inter.send(Messages.contest_vote_no_contributions)
            return

        await inter.send(Messages.contest_vote_top_contributions(number_of=number_of))
        for index in range(0, len(contributions), 5):
            await inter.send(''.join(contributions[index:index+5]))

    @cooldowns.default_cooldown
    @contest.sub_command(name='submit', description=Messages.contest_vote_submit_brief)
    async def submit(
        self,
        inter: disnake.ApplicationCommandInteraction,
        image: disnake.Attachment,
        description=commands.Param(default=None, max_length=1000)
    ):
        await inter.response.defer(ephemeral=True)
        if image.size > 25000000:   # 25MB
            await inter.send(Messages.contest_vote_file_too_big)
            return
        if 'image' not in image.content_type:
            await inter.send(Messages.contest_vote_not_image)
            return
        if inter.author.id in self.config.contest_vote_banned_users:
            await inter.send(Messages.contest_vote_banned_user)
            return

        user_contribution = ContestVoteDB.get_user(inter.author.id)
        if not user_contribution:
            contribution_id = ContestVoteDB.add_contribution(inter.author.id)
        else:
            if inter.author.id in self.config.contest_vote_no_limit_users:
                contribution_id = ContestVoteDB.add_contribution(inter.author.id)

            elif user_contribution.has_contributions >= self.config.contest_vote_max_contributions:
                await inter.send(Messages.contest_vote_max_contributions(
                    max_contributions=self.config.contest_vote_max_contributions)
                )
                return
            else:
                contribution_id = ContestVoteDB.add_contribution(inter.author.id)

        image = await image.to_file()

        trash = TrashView(custom_id='contest:delete')
        view = ContestView(self.bot)
        view.children.extend(trash.children)

        content = Messages.contest_vote_contribution(id=contribution_id)
        if description:
            content += f'Popis:\n{description}'

        message = await self.filter_channel.send(content, file=image, view=view)
        await message.pin()
        await message.add_reaction('👍')
        await message.add_reaction('👎')
        await inter.send(Messages.contest_vote_submit_success)

    def is_contest_room(self, ctx):
        return ctx.channel.id == self.config.contest_vote_channel

    @cooldowns.default_cooldown
    @commands.check(submod_plus)
    @commands.slash_command(name='contest_mod')
    async def contest_mod(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @contest_mod.sub_command(name='get_author', description=Messages.contest_vote_get_author_brief)
    async def get_author(self, inter: disnake.ApplicationCommandInteraction, id: int):
        await inter.response.defer(ephemeral=True)
        contribution_author_id = ContestVoteDB.get_contribution_author(id)
        if not contribution_author_id:
            await inter.send(Messages.contest_vote_contribution_not_found)
            return
        user = await self.bot.get_or_fetch_user(contribution_author_id)
        await inter.send(user.mention)

    @contest_mod.sub_command(name='start', description=Messages.contest_start_voting_brief)
    async def start_contest(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)
        messages = await self.contest_vote_channel.history().flatten()
        for message in messages:
            for emoji in self.emojis:
                await message.add_reaction(emoji)

        await inter.send(Messages.contest_vote_start_success)

    @contest_mod.sub_command(name='end', description=Messages.contest_end_voting_brief)
    async def end_contest(self, inter: disnake.ApplicationCommandInteraction):
        await inter.send(Messages.contest_vote_ending)
        messages = await self.contest_vote_channel.history().flatten()
        contributions = await get_top_contributions(self, messages)
        await self.contest_vote_channel.send(f"# Top 5 příspěvků\n{''.join(contributions)}")

        message = await inter.original_message()
        await message.edit(Messages.contest_vote_end_success)

    @contest_mod.sub_command(name='approve', description=Messages.contest_vote_approve_brief)
    async def approve(self, inter: disnake.ApplicationCommandInteraction, message: disnake.Message):
        if inter.channel.id != self.config.contest_vote_filter_channel:
            await inter.send(Messages.contest_vote_not_filter_channel, ephemeral=True)
            return

        file = await message.attachments[0].to_file()
        await self.contest_vote_channel.send(message.content, file=file)
        await message.edit(view=None)
        await message.unpin()
        await message.reply(Messages.contest_approve_success)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        """Handle button clicks"""
        if inter.component.custom_id != 'contest:delete':
            return

        await inter.response.send_modal(modal=DenyContributionModal(self.bot, inter))

    @commands.check(is_contest_room)
    async def handle_reaction(self, ctx: ReactionContext):
        """Allow only one reaction per user"""
        if ctx is None:
            return

        emoji_str = utils.str_emoji_id(ctx.emoji)
        message = ctx.message
        user = await self.bot.get_or_fetch_user(ctx.member.id)
        for r in message.reactions:
            if utils.str_emoji_id(r.emoji) == emoji_str:
                continue
            if await r.users().find(lambda x: x.id == user.id):
                await message.remove_reaction(ctx.emoji, user)
                return


def setup(bot):
    bot.add_cog(ContestVote(bot))
