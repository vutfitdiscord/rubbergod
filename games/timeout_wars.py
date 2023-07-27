"""
Containing game for 1. April called Timeout Wars.
When a message has X number of 🔇 reactions,
the bot will mute the user or on random mute the one with reaction.
"""

import csv
import os
import random
from datetime import datetime
from functools import cached_property
from typing import Union

import disnake
from disnake.ext import commands

import utils
from config.app_config import config
from config.messages import Messages


class TimeoutWars(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.immunity: dict[int, datetime] = {}
        self.ignored_messages = set()

    log_file = "timeout_wars"
    message_delete = "Smazání zprávy"

    @cached_property
    def timeout_wars_channel(self):
        return self.bot.get_channel(config.timeout_wars_log_channel)

    @commands.Cog.listener()
    async def on_ready(self):
        """create file if not exists on startup"""
        header = ["timeout_user(s)_id", "reacted_user(s)_id", "original_message_author", "reason", "datetime"]
        if not os.path.isfile(self.log_file):
            with open(self.log_file, "w") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(header)

    def write_log(self, timeout_users, reacted_users, original_message_author, reason):
        """write log to csv file"""
        with open(self.log_file, "a") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([timeout_users, reacted_users, original_message_author, reason, datetime.now()])

    async def send_embed_log(self, original_message, user: Union[list, disnake.Member], reason=None):
        """Embed template for Timeout wars"""
        embed = disnake.Embed(
            title="Moderace lidu",
            color=disnake.Color.yellow()
        )

        message = []
        if isinstance(user, list):
            for user in user:
                message.append(user.mention)
            embed.add_field(name="Umlčení uživatelé", value="\n".join(message), inline=False)
        else:
            embed.add_field(name="Umlčený uživatel", value=user.mention, inline=False)

        if reason == self.message_delete:
            embed.add_field(name="Důvod", value=reason, inline=False)

        embed.add_field(
            name="Link",
            value=f"[#{original_message.channel.name}]({original_message.jump_url})",
            inline=False
        )
        utils.add_author_footer(embed, original_message.author)
        await self.timeout_wars_channel.send(embed=embed)

    async def mute_users(self, original_message, channel, users, duration):
        """Mute users and send message to channel and log"""
        message = []

        for user in users:
            if self.get_immunity(user):
                message.append(Messages.timeout_wars_user_immunity(
                    user=user,
                    time=(self.immunity[user.id] - datetime.now()).total_seconds()
                    )
                )
            else:
                try:
                    await user.timeout(duration=duration, reason="Moderace lidu")
                    message.append(Messages.timeout_wars_user(
                        user=user.mention,
                        time=config.timeout_wars_timeout_time.total_seconds()//60)
                    )
                except disnake.Forbidden:
                    pass

        if message:
            await channel.send('\n'.join(message))
        await self.send_embed_log(original_message, users)

    async def mute_user(
        self,
        original_message,
        channel,
        user: disnake.Member,
        duration,
        reason="Moderace lidu"
    ):
        """Mute user and send message to channel and log"""
        if self.get_immunity(user):
            await channel.send(Messages.timeout_wars_user_immunity(
                    user=user,
                    time=(self.immunity[user.id] - datetime.now()).total_seconds()
                )
            )
        else:
            try:
                await user.timeout(duration=duration, reason=reason)
                if reason == self.message_delete:
                    await channel.send(Messages.timeout_wars_message_delete(
                        user=user.mention,
                        time=config.timeout_wars_timeout_time.total_seconds()//60
                    ))
                else:
                    await channel.send(Messages.timeout_wars_user(
                            user=user.mention,
                            time=config.timeout_wars_timeout_time.total_seconds()//60)
                    )
                await self.send_embed_log(original_message, user, reason)
            except disnake.Forbidden:
                pass

    def give_immunity(self, user, duration):
        """
        give immunity to user for duration time :D
        """
        self.immunity[user.id] = datetime.now() + duration

    def get_immunity(self, user) -> bool:
        """
        return True if user has immunity else False
        """
        immunity = self.immunity.get(user.id)
        if immunity is None:
            return False

        return immunity > datetime.now()

    async def all_mute(self, ctx, reaction):
        """
        give timeout to all users, who reacted mute
        """
        users = await reaction.users().flatten()

        await self.mute_users(ctx.message, ctx.channel, users, config.timeout_wars_timeout_time)

        timeouted = []
        for user in users:
            if not self.get_immunity(user):
                self.give_immunity(user, config.timeout_wars_immunity_time)
                timeouted.append(user.id)
        self.write_log(timeouted, [user.id for user in users], ctx.message.author.id, "all mute")

    async def random_mute(self, ctx, reaction):
        """
        give timeout to random user, who reacted mute
        """
        users = await reaction.users().flatten()
        user = random.choice(users)

        await self.mute_user(ctx.message, ctx.channel, user, config.timeout_wars_timeout_time)
        timeouted = []
        if not self.get_immunity(user):
            self.give_immunity(user, config.timeout_wars_immunity_time)
            timeouted.append(user.id)
        self.write_log(timeouted, [user.id for user in users], ctx.message.author.id, "random mute")

    async def author_mute(self, ctx, reaction):
        """
        give timeout to author of message (default case)
        """
        reaction_users = await reaction.users().flatten()

        # if user used slash command
        if ctx.message.interaction is not None:
            author = await ctx.guild.get_or_fetch_member(ctx.message.interaction.user.id)
        else:
            author = ctx.message.author

        await self.mute_user(ctx.message, ctx.channel, author, config.timeout_wars_timeout_time)
        timeouted = []
        if not self.get_immunity(author):
            self.give_immunity(author, config.timeout_wars_immunity_time)
            timeouted.append(author.id)
        self.write_log(timeouted, [user.id for user in reaction_users], author.id, "author mute")

    async def handle_reaction(self, ctx):
        """
        if the message has X or more 'mute' emojis mute the user
        or on random select one reaction and mute the user.
        """

        message = ctx.message
        mute_reaction = None
        # skip if somebody already got mute from this message
        if message.id in self.ignored_messages:
            return

        # find mute reaction
        for reaction in message.reactions:
            if reaction.emoji == "🔇":
                mute_reaction = reaction
                break

        # skip if there is less than timeout_wars_reaction_count reactions
        if (
            mute_reaction is None or
            mute_reaction.count < config.timeout_wars_reaction_count
        ):
            return

        # add this message to ignorelist
        self.ignored_messages.add(message.id)

        # randomly choose one of 3 scenarios
        r = random.randint(1, 100)

        if r <= config.timeout_wars_chance_all_mute:
            await self.all_mute(ctx, mute_reaction)
            return
        r -= config.timeout_wars_chance_all_mute

        if r <= config.timeout_wars_chance_random_mute:
            await self.random_mute(ctx, mute_reaction)
            return
        r -= config.timeout_wars_chance_random_mute

        # default scenario
        await self.author_mute(ctx, mute_reaction)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: disnake.RawMessageDeleteEvent):
        if payload.cached_message is None:
            return
        for reaction in payload.cached_message.reactions:
            if reaction.emoji == "🔇":
                await self.mute_user(
                    payload.cached_message,
                    payload.cached_message.channel,
                    payload.cached_message.author,
                    config.timeout_wars_timeout_time,
                    reason=self.message_delete
                )


def setup(bot):
    bot.add_cog(TimeoutWars(bot))
