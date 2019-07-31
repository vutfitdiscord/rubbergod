import asyncio

import discord
from discord import Emoji
from discord.ext.commands import Bot
from emoji import UNICODE_EMOJI

import utils
from config import config, messages
from features.base_feature import BaseFeature
from repository.karma_repo import KarmaRepository

cfg = config.Config
msg = messages.Messages


def test_emoji(db_emoji: bytearray, server_emoji: Emoji):
    try:
        custom_emoji = int(db_emoji)
        return custom_emoji == server_emoji.id
    except ValueError:
        return False


class Karma(BaseFeature):
    def __init__(self, bot: Bot, karma_repository: KarmaRepository):
        super().__init__(bot)
        self.repo = karma_repository

    async def emoji_process_vote(self, channel, emoji):
        delay = cfg.vote_minutes * 60
        message = await channel.send(
            "{}\n{}".format(msg.karma_vote_message
                            .format(emote=str(emoji)),
                            msg.karma_vote_info
                            .format(delay=str(delay // 60),
                                    minimum=str(cfg.vote_minimum))))

        await message.add_reaction("✅")
        await message.add_reaction("❌")
        await message.add_reaction("0⃣")
        await asyncio.sleep(delay)

        message = await channel.fetch_message(message.id)

        plus = 0
        minus = 0
        neutral = 0

        for reaction in message.reactions:
            if reaction.emoji == "✅":
                plus = reaction.count - 1
            elif reaction.emoji == "❌":
                minus = reaction.count - 1
            elif reaction.emoji == "0⃣":
                neutral = reaction.count - 1

        if plus + minus + neutral < cfg.vote_minimum:
            return None

        if plus > minus + neutral:
            return 1
        elif minus > plus + neutral:
            return -1
        else:
            return 0

    async def emoji_vote_value(self, message):
        if len(message.content.split()) != 2:
            await message.channel.send(
                msg.karma_vote_format)
            return

        emojis = self.repo.get_all_emojis()

        for server_emoji in message.guild.emojis:
            if not server_emoji.animated:
                e = list(
                    filter(
                        lambda x: test_emoji(x[0], server_emoji),
                        emojis))

                if len(e) == 0:
                    vote_value = await self.emoji_process_vote(message.channel,
                                                               server_emoji)
                    emoji = server_emoji
                    break
        else:
            await message.channel.send(msg.karma_vote_allvoted)
            return

        if vote_value is None:
            await message.channel.send(
                msg.karma_vote_notpassed
                .format(emote=str(emoji),
                        minimum=str(cfg.vote_minimum)))

        else:
            self.repo.set_emoji_value(emoji, vote_value)
            await message.channel.send(
                msg.karma_vote_result
                .format(emote=str(emoji),
                        result=str(vote_value)))

    async def emoji_revote_value(self, message):
        content = message.content.split()
        if len(content) != 3:
            await message.channel.send(msg.karma_revote_format)
            return

        emoji = content[2]
        if len(emoji) != 1 or emoji[0] not in UNICODE_EMOJI:
            try:
                emoji_id = int(emoji.split(':')[2][:-1])
                emoji = await message.channel.guild.fetch_emoji(emoji_id)
            except (ValueError, IndexError):
                await message.channel.send(msg.karma_revote_format)
                return
            except discord.NotFound:
                await message.channel.send(msg.karma_emote_not_found)
                return

        vote_value = await self.emoji_process_vote(message.channel, emoji)

        if vote_value is not None:
            self.repo.set_emoji_value(emoji, vote_value)
            await message.channel.send(
                msg.karma_vote_result
                .format(emote=str(emoji), result=str(vote_value)))
        else:
            await message.channel.send(
                msg.karma_vote_notpassed
                .format(emote=str(emoji),
                        minimum=str(cfg.vote_minimum)))

    async def emoji_get_value(self, message):
        content = message.content.split()
        if len(content) != 3:
            return await self.emoji_list_all_values(message.channel)

        emoji = content[2]
        if len(emoji) != 1 or emoji[0] not in UNICODE_EMOJI:
            try:
                emoji_id = int(emoji.split(':')[2][:-1])
                emoji = await message.channel.guild.fetch_emoji(emoji_id)
            except (ValueError, IndexError):
                await message.channel.send(msg.karma_get_format)
                return
            except discord.NotFound:
                await message.channel.send(msg.karma_emote_not_found)
                return

        val = self.repo.emoji_value_raw(emoji)

        if val is not None:
            await message.channel.send(
                msg.karma_get
                .format(emote=str(emoji), value=str(val)))
        else:
            await message.channel.send(
                msg.karma_get_emote_not_voted
                .format(emote=str(emoji)))

    async def __make_emoji_list(self, guild, emojis):
        message = ""
        errors = ""

        # Fetch all custom server emoji
        # They will be saved in the guild.emojis list
        await guild.fetch_emojis()

        for cnt, emoji_id in enumerate(emojis):
            if cnt % 8 == 0 and cnt:
                message += "\n"

            try:
                # Try and find the emoji in the server custom emoji list (match by id)
                # if the current emoji_id is not an int, it's a unicode emoji,
                # we'll handle that in the except ValueError part.
                # If it is an int and it's not found in the emoji list, it will try to fetch
                # it once again and as that will probably fail anyway, it'll jump to
                # the discord.NotFound handler which will add it to the error message
                emoji = next((x for x in guild.emojis if x.id == int(emoji_id)), None)
                if emoji is None:
                    emoji = await guild.fetch_emoji(int(emoji_id))

                message += str(emoji)

            except ValueError:
                if isinstance(emoji_id, bytearray):
                    message += emoji_id.decode()
                else:
                    message += str(emoji_id)

            except discord.NotFound:
                errors += str(emoji_id) + ", "

        return message, errors

    async def emoji_list_all_values(self, channel):
        errors = ""

        pos_msg = await self.__make_emoji_list(channel.guild,
                                               self.repo.get_positive_emojis())
        neg_msg = await self.__make_emoji_list(channel.guild,
                                               self.repo.get_negative_emojis())

        errors += pos_msg[1] + neg_msg[1]

        try:
            await channel.send("Hodnota 1:\n" + pos_msg[0])
            await channel.send("Hodnota -1:\n" + neg_msg[0])
        except discord.errors.HTTPException:
            pass  # TODO: error handling?

        if errors != "":
            await self.log_channel.send("{}\n{}".format(msg.toaster_pls,
                                                        errors))

    async def karma_give(self, message):
        input_string = message.content.split()
        if len(input_string) < 4:
            await message.channel.send(msg.karma_give_format)
        else:
            try:
                number = int(input_string[2])
            except ValueError:
                await message.channel.send(
                    msg.karma_give_format_number.format(
                        input=input_string[2])
                )
                return
            for member in message.mentions:
                self.repo.update_karma(member, message.author, number)
            if number >= 0:
                await message.channel.send(msg.karma_give_success)
            else:
                await message.channel.send(
                    msg.karma_give_negative_success
                )

    def karma_get(self, author):
        k = self.repo.get_karma(author.id, "get")

        return msg.karma_own.format(user=utils.generate_mention(
                                    author.id),
                                    karma=str(k[0]), pos=str(k[1]))

    def karma_giving_get(self, author):
        k = self.repo.get_karma(author.id, "give")

        return msg.karma_given.format(user=utils.generate_mention(
                                      author.id),
                                      karma_pos=str(k[0]),
                                      karma_pos_pos=str(k[2]),
                                      karma_neg=str(k[1]),
                                      karma_neg_pos=str(k[3]))

    async def leaderboard(self, channel, action, order):
        output = "\u200b\n==================\n "
        if action == 'give':
            database = 'bot_karma_giving'
            if order == "DESC":
                database_index = 1
                column = 'positive'
                output += "KARMA GIVINGBOARD \n"
            else:
                database_index = 2
                order = "DESC"
                column = 'negative'
                output += "KARMA ISHABOARD \n"
        elif action == 'get':
            database_index = 1
            database = 'bot_karma'
            column = 'karma'
            if order == "DESC":
                output += "KARMA LEADERBOARD \n"
            else:
                output += "KARMA BAJKARBOARD \n"
        else:
            raise Exception('Action neni get/give')
        output += "==================\n"

        board = self.repo.get_leaderboard(database, column, order)
        guild = self.bot.get_guild(cfg.guild_id)

        for i, user in enumerate(board, 1):
            username = guild.get_member(int(user[0]))
            if username is None:
                continue
            username = str(username.name)
            line = '{} – {}: {} pts\n'.format(i, username,
                                              user[database_index])
            output += line

        await channel.send(output)
