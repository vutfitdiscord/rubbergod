import discord
from discord.ext.commands import Bot

import utils
from config.app_config import Config
from config.messages import Messages
from features.base_feature import BaseFeature
from repository.karma_repo import KarmaRepository


class Reaction(BaseFeature):

    def __init__(self, bot: Bot, karma_repository: KarmaRepository):
        super().__init__(bot)
        self.karma_repo = karma_repository

    async def add(self, payload):
        ctx = await utils.reaction_get_ctx(self.bot, payload)
        if ctx is None:
            return
        if ctx['emoji'] == "⏹️":
            return
            # grillbot emoji for removing message causes errors
        if ctx['message'].content.startswith(Config.role_string) or\
           ctx['channel'].id in Config.role_channels:
            return
        elif ctx['message'].content.startswith(Messages.karma_vote_message_hack):
            if ctx['emoji'] not in ["✅", "❌", "0⃣"]:
                await ctx['message'].remove_reaction(ctx['emoji'], ctx['member'])
            else:
                users = []
                for reaction in ctx['message'].reactions:
                    users.append(await reaction.users().flatten())
                # Flatten the final list
                users = [x for y in users for x in y]
                if users.count(ctx['member']) > 1:
                    await ctx['message'].remove_reaction(ctx['emoji'], ctx['member'])
        elif ctx['member'].id != ctx['message'].author.id and\
                ctx['guild'].id == Config.guild_id and\
                ctx['message'].channel.id not in \
                Config.karma_banned_channels and \
                Config.karma_ban_role_id not in map(lambda x: x.id, ctx['member'].roles):
            if isinstance(ctx['emoji'], str):
                self.karma_repo.karma_emoji(ctx['message'].author, ctx['member'], ctx['emoji'])
            else:
                self.karma_repo.karma_emoji(ctx['message'].author, ctx['member'], ctx['emoji'].id)

    async def remove(self, payload):
        ctx = await utils.reaction_get_ctx(self.bot, payload)
        if ctx is None:
            return

        if ctx['member'].id != ctx['message'].author.id and \
                ctx['guild'].id == Config.guild_id and \
                ctx['message'].channel.id not in \
                Config.karma_banned_channels and \
                Config.karma_ban_role_id not in map(lambda x: x.id,
                                                    ctx['member'].roles):
            if isinstance(ctx['emoji'], str):
                self.karma_repo.karma_emoji_remove(ctx['message'].author,
                                                   ctx['member'], ctx['emoji'])
            else:
                self.karma_repo.karma_emoji_remove(
                    ctx['message'].author, ctx['member'], ctx['emoji'].id)

