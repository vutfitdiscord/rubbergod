import datetime
import discord
from discord.ext.commands import Bot
import re

import utils
from utils import fill_message
from config.config import Config
from config.messages import Messages
from features.base_feature import BaseFeature
from features.acl import Acl
from features.review import Review
from repository.karma_repo import KarmaRepository
from repository.acl_repo import AclRepository
from repository.review_repo import ReviewRepository

acl_repo = AclRepository()
acl = Acl(acl_repo)
review_r = ReviewRepository()


class Reaction(BaseFeature):

    def __init__(self, bot: Bot, karma_repository: KarmaRepository):
        super().__init__(bot)
        self.karma_repo = karma_repository
        self.review = Review(bot)

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

        embed.set_footer(text=f"Page {page} | Commit {utils.git_hash()}",
                         icon_url="https://cdn.discordapp.com/avatars/"
                                  "560917571663298568/b93e8c1e93c2d18b"
                                  "fbd226a0b614cf57.png?size=32")
        return embed

    # Returns list of role names and emotes that represent them
    async def get_join_role_data(self, message):
        input_string = message.content
        input_string = input_string.replace("**", "")
        try:
            if input_string.startswith(Config.role_string):
                input_string = input_string[input_string.index('\n') + 1:]
            input_string = input_string.rstrip().split('\n')
        except ValueError:
            await message.channel.send(fill_message("role_format", user=message.author.id))
            return None
        output = []
        for line in input_string:
            try:
                out = line.split(" - ", 1)[0].split()
                out = [out[1], out[0]]
                output.append(out)
            except:
                await message.channel.send(fill_message("role_invalid_line",
                                           user=message.author.id, line=line))
        for line in output:
            if "<#" in line[0]:
                line[0] = line[0].replace("<#", "")
                line[0] = line[0].replace(">", "")
                try:
                    line[0] = int(line[0])
                except:
                    await message.channel.send(fill_message("role_invalid_line",
                                            user=message.author.id, line=line[0]))
        return output

    # Adds reactions to message
    async def message_role_reactions(self, message, data):
        if message.channel.type is not discord.ChannelType.text:
            await message.channel.send(Messages.role_not_on_server)
            guild = self.bot.get_guild(Config.guild_id)
        else:
            guild = message.guild
        for line in data:
            not_role = discord.utils.get(guild.roles, name=line[0]) is None
            if isinstance(line[0], int) or line[0].isdigit():
                not_channel = discord.utils.get(guild.channels,
                                                id=int(line[0])) is None
            else:
                not_channel = line[0][0] != "#" or\
                    discord.utils.get(guild.channels,
                                      name=line[0][1:].lower()) is None
            if not_role and not_channel:
                await message.channel.send(fill_message("role_not_role",
                                        user=message.author.id, not_role=line[0]))
            else:
                try:
                    await message.add_reaction(line[1])
                except discord.errors.HTTPException:
                    await message.channel.send(fill_message("role_invalid_emote",
                                            user=message.author.id, not_role=line[1], role=line[0]))

    async def add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return
        if channel.type is discord.ChannelType.text:
            guild = channel.guild
        else:
            guild = self.bot.get_guild(Config.guild_id)
            if guild is None:
                raise Exception("Nemuzu najit guildu podle config.guild_id")
        member = guild.get_member(payload.user_id)

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.errors.NotFound:
            return

        if member is None or message is None or member.bot:
            return

        if payload.emoji.is_custom_emoji():
            emoji = self.bot.get_emoji(payload.emoji.id)
            if emoji is None:
                emoji = payload.emoji
        else:
            emoji = payload.emoji.name
        if emoji == "⏹️":
            return
            # grillbot emoji for removing message causes errors
        if message.content.startswith(Config.role_string) or\
           channel.id in Config.role_channels:
            role_data = await self.get_join_role_data(message)
            for line in role_data:
                if str(emoji) == line[1]:
                    await self.add_role_on_reaction(line[0], member,
                                                    message.channel,
                                                    guild)
                    break
            else:
                await message.remove_reaction(emoji, member)
        elif message.content.startswith(Messages.karma_vote_message_hack):
            if emoji not in ["✅", "❌", "0⃣"]:
                await message.remove_reaction(emoji, member)
            else:
                users = []
                for reaction in message.reactions:
                    users.append(await reaction.users().flatten())
                # Flatten the final list
                users = [x for y in users for x in y]
                if users.count(member) > 1:
                    await message.remove_reaction(emoji, member)
        elif message.embeds and message.embeds[0].title == "Rubbergod":
            if emoji in ["◀", "▶"]:
                page = int(message.embeds[0].footer.text[5])
                next_page = self.pagination_next(emoji, page,
                                                 len(Messages.info))
                if next_page:
                    embed = self.make_embed(next_page)
                    await message.edit(embed=embed)
            try:
                await message.remove_reaction(emoji, member)
            except:
                pass
        elif message.embeds and\
                message.embeds[0].title is not discord.Embed.Empty and\
                re.match(".* reviews", message.embeds[0].title):
            subject = message.embeds[0].title.split(' ', 1)[0]
            footer = message.embeds[0].footer.text.split('|')[0]
            pos = footer.find('/')
            try:
                page = int(footer[8:pos])
                max_page = int(footer[(pos + 1):])
            except ValueError:
                await message.edit(content=Messages.reviews_page_e, embed=None)
                return
            tier_average = message.embeds[0].description[-1]
            if emoji in ["◀", "▶", "⏪"]:
                next_page = self.pagination_next(emoji, page, max_page)
                if next_page:
                    review = review_r.get_subject_reviews(subject)
                    if review.count() >= next_page:
                        review = review.all()[next_page - 1].Review
                        next_page = str(next_page) + "/" + str(max_page)
                        embed = self.review.make_embed(
                            review, subject, tier_average, next_page)
                        await message.edit(embed=embed)
            elif emoji in ["👍", "👎", "🛑"]:
                review = review_r.get_subject_reviews(subject)[page - 1].Review
                if str(member.id) != review.member_ID:
                    review_id = review.id
                    if emoji == "👍":
                        self.review.add_vote(review_id, True, str(member.id))
                    elif emoji == "👎":
                        self.review.add_vote(review_id, False, str(member.id))
                    elif emoji == "🛑":
                        review_r.remove_vote(
                            review_id, str(member.id))
                    page = str(page) + "/" + str(max_page)
                    embed = self.review.make_embed(
                        review, subject, tier_average, page)
                    await message.edit(embed=embed)
            elif emoji in ["🔼", "🔽"]:
                if message.embeds[0].fields[3].name == "Text page":
                    review = review_r.get_subject_reviews(
                        subject)
                    if review:
                        await message.remove_reaction(emoji, member)
                        return
                    review = review[page - 1].Review
                    text_page = message.embeds[0].fields[3].value
                    pos = message.embeds[0].fields[3].value.find('/')
                    max_text_page = int(text_page[(pos + 1):])
                    text_page = int(text_page[:pos])
                    next_text_page = self.pagination_next(emoji, page,
                                                          max_text_page)
                    if next_text_page:
                        page = str(page) + "/" + str(max_page)
                        embed = self.review.make_embed(
                            review, subject, tier_average, page)
                        embed = self.review.change_text_page(
                            review, embed, next_text_page, max_text_page)
                        await message.edit(embed=embed)
            try:
                await message.remove_reaction(emoji, member)
            except:
                pass
        elif member.id != message.author.id and\
                guild.id == Config.guild_id and\
                message.channel.id not in \
                Config.karma_banned_channels and \
                Config.karma_ban_role_id not in map(lambda x: x.id,
                                                    member.roles):
            if isinstance(emoji, str):
                self.karma_repo.karma_emoji(message.author, member, emoji)
            else:
                self.karma_repo.karma_emoji(message.author, member, emoji.id)

        # if the message has X or more 'pin' emojis pin the message
        if emoji == '📌':
            for reaction in message.reactions:
                if reaction.emoji == '📌' and \
                   reaction.count >= Config.pin_count and \
                   not message.pinned:
                    embed = discord.Embed(title="📌 Auto pin message log",
                                          color=0xeee657)
                    users = await reaction.users().flatten()
                    user_names = ', '.join([user.name for user in users])
                    message_link = Messages.message_link_prefix +\
                        str(message.channel.id) + '/' +\
                        str(message.id)
                    embed.add_field(name="Users", value=user_names)
                    embed.add_field(name="In channel", value=message.channel)
                    embed.add_field(name="Message",
                                    value=message_link, inline=False)
                    embed.set_footer(
                        text=datetime.datetime.now().replace(microsecond=0)
                    )
                    channel = self.bot.get_channel(Config.log_channel)
                    await channel.send(embed=embed)
                    try:
                        await message.pin()
                    except discord.HTTPException:
                        break

    async def remove(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return
        if channel.type is discord.ChannelType.text:
            guild = channel.guild
        else:
            guild = self.bot.get_guild(Config.guild_id)
            if guild is None:
                raise Exception("Nemuzu najit guildu podle config.guild_id")
        member = guild.get_member(payload.user_id)

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.errors.NotFound:
            return

        if member is None or message is None or member.bot:
            return

        if payload.emoji.is_custom_emoji():
            emoji = self.bot.get_emoji(payload.emoji.id)
            if emoji is None:
                emoji = payload.emoji
        else:
            emoji = payload.emoji.name
        if message.content.startswith(Config.role_string) or\
           channel.id in Config.role_channels:
            role_data = await self.get_join_role_data(message)
            for line in role_data:
                if str(emoji) == line[1]:
                    await self.remove_role_on_reaction(line[0], member,
                                                       message.channel,
                                                       guild)
                    break
        elif member.id != message.author.id and \
                guild.id == Config.guild_id and \
                message.channel.id not in \
                Config.karma_banned_channels and \
                Config.karma_ban_role_id not in map(lambda x: x.id,
                                                    member.roles):
            if isinstance(emoji, str):
                self.karma_repo.karma_emoji_remove(message.author,
                                                   member, emoji)
            else:
                self.karma_repo.karma_emoji_remove(
                    message.author, member, emoji.id)

    # Adds a role for user based on reaction
    async def add_role_on_reaction(self, target, member, channel, guild):
        role = discord.utils.get(guild.roles,
                                 name=target)
        if role is not None:
            if acl.get_perms(member.id, member.top_role,
                             role.id, guild.roles):
                await member.add_roles(role)
            else:
                bot_room = self.bot.get_channel(Config.bot_room)
                await bot_room.send(fill_message("role_add_denied",
                                        user=member.id, role=role.name))
        else:
            try:
                channel = discord.utils.get(guild.channels, id=int(target))
            except ValueError:
                channel = None
            if channel is None:
                channel = discord.utils.get(guild.channels,
                                            name=target[1:].lower())
            if channel is None:
                return
            perms = acl.get_perms(member.id, member.top_role,
                                  channel.id, guild.roles)
            # TODO give perms based on the int (like read-only)
            if perms:
                await channel.set_permissions(member, read_messages=True)
            else:
                bot_room = self.bot.get_channel(Config.bot_room)
                await bot_room.send(fill_message("role_add_denied",
                                        user=member.id, role=channel.name))

    # Removes a role for user based on reaction
    async def remove_role_on_reaction(self, target, member, channel, guild):
        role = discord.utils.get(guild.roles,
                                 name=target)
        if role is not None:
            if role in member.roles:
                if acl.get_perms(member.id, member.top_role,
                                 role.id, guild.roles):
                    await member.remove_roles(role)
                else:
                    bot_room = self.bot.get_channel(Config.bot_room)
                    await bot_room.send(fill_message("role_remove_denied",
                                            user=member.id, role=role.name))
        else:
            try:
                channel = discord.utils.get(guild.channels, id=int(target))
            except ValueError:
                channel = None
            if channel is None:
                channel = discord.utils.get(guild.channels,
                                            name=target[1:].lower())
            if channel is None:
                return
            perms = acl.get_perms(member.id, member.top_role,
                                  channel.id, guild.roles)
            if perms:
                await channel.set_permissions(member, read_messages=None,
                                              send_messages=None)
            else:
                bot_room = self.bot.get_channel(Config.bot_room)
                await bot_room.send(fill_message("role_remove_denied",
                                        user=member.id, role=channel.name))

    def pagination_next(self, emoji, page, max_page):
        if emoji in ["▶", "🔽"]:
            next_page = page + 1
        elif emoji in ["◀", "🔼"]:
            next_page = page - 1
        elif emoji == "⏪":
            next_page = 1
        if 1 <= next_page <= max_page:
            return next_page
        else:
            return 0
