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

    def make_embed(self, page):
        embed = discord.Embed(title="Rubbergod",
                              description="Nejlepší a nejúžasnější bot ever.",
                              color=0xeee657)

        prefix = Config.default_prefix

        embed.add_field(name="Autor", value="Toaster#1111")

        # Shows the number of servers the bot is member of.
        embed.add_field(name="Počet serverů s touto instancí bota",
                        value=f"{len(self.bot.guilds)}")

        embed.add_field(name="\u200b", value="Příkazy:", inline=False)

        info = Messages.info[page - 1]

        for command in info:
            embed.add_field(name=prefix + command[0],
                            value=command[1],
                            inline=False)

        git_hash = utils.git_hash()
        footer_text = f"Commit {git_hash}"

        if len(Messages.info) > 1:
            footer_text = f"Page {page} | {footer_text}"

        embed.set_footer(text=footer_text, icon_url="https://cdn.discordapp.com/avatars/"
                         "560917571663298568/b93e8c1e93c2d18b"
                         "fbd226a0b614cf57.png?size=32")
        return embed

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
        elif ctx['message'].embeds and ctx['message'].embeds[0].title == "Rubbergod":
            if ctx['emoji'] in ["◀", "▶"]:
                page = int(ctx['message'].embeds[0].footer.text[5])
                next_page = utils.pagination_next(ctx['emoji'], page,
                                                  len(Messages.info))
                if next_page:
                    embed = self.make_embed(next_page)
                    await ctx['message'].edit(embed=embed)
            try:
                await ctx['message'].remove_reaction(ctx['emoji'], ctx['member'])
            except Exception:
                pass
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

