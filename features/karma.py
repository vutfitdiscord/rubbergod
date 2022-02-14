import asyncio
import math
import re

import disnake
from disnake import Emoji, TextChannel, Member
from disnake.ext.commands import Bot
from emoji import demojize

import utils
from config.app_config import config as cfg
from config.messages import Messages as msg
from features.base_feature import BaseFeature
from repository.karma_repo import KarmaRepository
from repository.database.karma import Karma as Database_karma


def test_emoji(db_emoji: bytearray, server_emoji: Emoji):
    try:
        custom_emoji = int(db_emoji)
        return custom_emoji == server_emoji.id
    except ValueError:
        return False


def is_unicode(text):
    demojized = demojize(text)
    if demojized.count(':') != 2:
        return False
    if demojized.split(':')[2] != '':
        return False
    return demojized != text


class Karma(BaseFeature):
    def __init__(self, bot: Bot, karma_repository: KarmaRepository):
        super().__init__(bot)
        self.repo = karma_repository

    async def emoji_process_vote(self, channel, emoji):
        delay = cfg.vote_minutes * 60
        message = utils.fill_message("karma_vote_message", emote=str(emoji))
        message += '\n'
        message += utils.fill_message("karma_vote_info", delay=str(delay//60), minimum=str(cfg.vote_minimum))
        message = await channel.send(message)
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
                        lambda x: test_emoji(x.emoji_ID, server_emoji),
                        emojis))

                if len(e) == 0:
                    self.repo.set_emoji_value(server_emoji, 0)
                    vote_value = await self.emoji_process_vote(message.channel,
                                                               server_emoji)
                    emoji = server_emoji  # Save for use outside loop
                    break
        else:
            await message.channel.send(msg.karma_vote_allvoted)
            return

        if vote_value is None:
            self.repo.remove_emoji(emoji)
            await message.channel.send(utils.fill_message("karma_vote_notpassed",
                                       emote=str(emoji), minimum=str(cfg.vote_minimum)))

        else:
            self.repo.set_emoji_value(emoji, vote_value)
            await message.channel.send(utils.fill_message("karma_vote_result",
                                       emote=str(emoji), result=str(vote_value)))

    async def emoji_revote_value(self, message):
        content = message.content.split()
        if len(content) != 3:
            await message.channel.send(msg.karma_revote_format)
            return

        emoji = content[2]
        if not is_unicode(emoji):
            try:
                emoji_id = int(emoji.split(':')[2][:-1])
                emoji = await message.channel.guild.fetch_emoji(emoji_id)
            except (ValueError, IndexError):
                await message.channel.send(msg.karma_revote_format)
                return
            except disnake.NotFound:
                await message.channel.send(msg.karma_emote_not_found)
                return

        vote_value = await self.emoji_process_vote(message.channel, emoji)

        if vote_value is not None:
            self.repo.set_emoji_value(emoji, vote_value)
            await message.channel.send(utils.fill_message("karma_vote_result",
                                       emote=str(emoji), result=str(vote_value)))
        else:
            await message.channel.send(utils.fill_message("karma_vote_notpassed",
                                       emote=str(emoji), minimum=str(cfg.vote_minimum)))

    async def emoji_get_value(self, message):
        content = message.content.split()
        if len(content) != 3:
            await message.channel.send(msg.karma_get_format)
            return

        emoji = content[2]
        if not is_unicode(emoji):
            try:
                emoji_id = int(emoji.split(':')[2][:-1])
                emoji = await message.channel.guild.fetch_emoji(emoji_id)
            except (ValueError, IndexError):
                await message.channel.send(msg.karma_get_format)
                return
            except disnake.NotFound:
                await message.channel.send(msg.karma_emote_not_found)
                return

        val = self.repo.emoji_value_raw(emoji)

        if val is not None:
            await message.channel.send(utils.fill_message("karma_get", emote=str(emoji), value=str(val)))
        else:
            await message.channel.send(utils.fill_message("karma_get_emote_not_voted", emote=str(emoji)))

    async def __make_emoji_list(self, guild, emojis):
        message = []
        line = ""
        is_error = False

        # Fetch all custom server emoji
        # They will be saved in the guild.emojis list
        await guild.fetch_emojis()

        for cnt, emoji_id in enumerate(emojis):
            if cnt % 8 == 0 and cnt:
                line += "\n"
            if cnt % 24 == 0 and cnt:
                message.append(line)
                line = ""

            try:
                # Try and find the emoji in the server custom emoji list
                # (match by id) if the current emoji_id is not an int,
                # it's a unicode emoji, we'll handle that in the except
                # ValueError part. If it is an int and it's not found
                # in the emoji list, it will try to fetch it once again
                # and as that will probably fail anyway, it'll jump to
                # the disnake.NotFound handler which will add it to
                # the error message
                emoji = next((x for x in guild.emojis if x.id == int(emoji_id)), None)

                if emoji is None:
                    emoji = await guild.fetch_emoji(int(emoji_id))

                line += str(emoji)

            except ValueError:
                if isinstance(emoji_id, bytearray):
                    line += emoji_id.decode()
                else:
                    line += str(emoji_id)

            except disnake.NotFound:
                is_error = True
                if isinstance(emoji_id, bytearray):
                    self.repo.remove_emoji(emoji_id.decode())
                else:
                    self.repo.remove_emoji(str(emoji_id))

        message.append(line)
        message = [line for line in message if line != ""]
        return message, is_error

    async def emoji_list_all_values(self, channel):
        error = False
        for value in ['1', '-1']:
            emojis, is_error = await self.__make_emoji_list(
                    channel.guild,
                    self.repo.get_ids_of_emojis_valued(value))
            error |= is_error
            try:
                await channel.send("Hodnota " + value + ":")
                for line in emojis:
                    await channel.send(line)
            except disnake.errors.HTTPException:
                pass  # TODO: error handling?

        if error:
            channel = await self.bot.fetch_channel(cfg.bot_dev_channel)
            await channel.send(msg.karma_get_missing)

    async def karma_give(self, message):
        input_string = message.content.split()
        if len(input_string) < 4:
            await message.channel.send(msg.karma_give_format)
        else:
            try:
                number = int(input_string[2])
            except ValueError:
                await message.channel.send(utils.fill_message("karma_give_format_number",
                                                              input=input_string[2]))
                return
            for member in message.mentions:
                self.repo.update_karma(member, message.author, number)
            if number >= 0:
                await message.channel.send(msg.karma_give_success)
            else:
                await message.channel.send(
                    msg.karma_give_negative_success
                )

    async def karma_transfer(self, message: TextChannel):
        input_string = message.content.split()
        if len(input_string) < 4 or len(message.mentions) < 2:
            await message.channel.send(msg.karma_transfer_format)
            return

        try:
            from_user: Member = message.mentions[0]
            to_user: Member = message.mentions[1]

            transfered = self.repo.transfer_karma(from_user, to_user)
            formated_message = utils.fill_message("karma_transfer_complete", from_user=from_user.name,
                                                  to_user=to_user.name, karma=transfered.karma,
                                                  positive=transfered.positive, negative=transfered.negative)

            await self.reply_to_channel(message.channel, formated_message)
        except ValueError:
            await self.reply_to_channel(message.channel, msg.karma_transfer_format)
            return

    def karma_get(self, author, target=None):
        if target is None:
            target = author
        k = self.repo.get_karma(target.id)
        return utils.fill_message(
            "karma",
            user=author.id,
            karma=k.karma.value,
            order=k.karma.position,
            target=target.display_name,
            karma_pos=k.positive.value,
            karma_pos_order=k.positive.position,
            karma_neg=k.negative.value,
            karma_neg_order=k.negative.position
        )

    async def message_karma(self, author: disnake.User, msg: disnake.Message):
        reactions = msg.reactions
        colour = 0x6d6a69
        output = {'-1': [], '1': [], '0': []}
        karma = 0
        for react in reactions:
            emoji = react.emoji
            val = self.repo.emoji_value_raw(emoji)
            if val == 1:
                output['1'].append(emoji)
                karma += react.count
                async for user in react.users():
                    if user.id == msg.author.id:
                        karma -= 1
                        break
            elif val == -1:
                output['-1'].append(emoji)
                karma -= react.count
                async for user in react.users():
                    if user.id == msg.author.id:
                        karma += 1
                        break
            else:
                output['0'].append(emoji)
        embed = disnake.Embed(title='Karma zprávy')
        embed.add_field(name="Zpráva", value=msg.jump_url, inline=False)
        for key in ['1', '-1', '0']:
            if output[key]:
                message = ""
                for emoji in output[key]:
                    message += str(emoji) + ' '
                if key == '1':
                    name = 'Pozitivní'
                elif key == '0':
                    name = 'Neutrální'
                else:
                    name = 'Negativní'
                embed.add_field(name=name, value=message, inline=False)
        if karma > 0:
            colour = 0x34cb0b
        elif karma < 0:
            colour = 0xcb410b
        embed.colour = colour
        embed.add_field(name='Celková karma za zprávu:', value=karma, inline=False)
        utils.add_author_footer(embed, author)
        return embed

    async def leaderboard(self, ctx: disnake.ext.commands.Context, action, order, start=1):
        if action == 'give':
            if order == "DESC":
                column = 'positive'
                attribute = Database_karma.positive.desc()
                emote = "<:peepolove:851025266553258044>"
                title = emote + "KARMA GIVINGBOARD " + emote
            else:
                column = 'negative'
                attribute = Database_karma.negative.desc()
                emote = "<:ishagrin:638277508651024394>"
                title = emote + " KARMA ISHABOARD " + emote
        elif action == 'get':
            column = 'karma'
            if order == "DESC":
                attribute = Database_karma.karma.desc()
                emote = ":trophy:"
                title = emote + " KARMA LEADERBOARD " + emote
            else:
                attribute = Database_karma.karma
                emote = "<:coolStoryBob:851029030689701898>"
                title = emote + " KARMA BAJKARBOARD " + emote
        else:
            raise Exception('Action neni get/give')

        output = self.gen_leaderboard_content(attribute, start, column)

        embed = disnake.Embed(title=title, description=output)
        utils.add_author_footer(embed, ctx.author)

        if action == "get" and order == "DESC":
            value_num = math.ceil(start / cfg.karma_grillbot_leaderboard_size)
            value = msg.karma_web if value_num == 1 else f"{msg.karma_web}{value_num}"
            embed.add_field(name=msg.karma_web_title, value=value)

        message = await ctx.send(embed=embed)

        await message.add_reaction("⏪")
        await message.add_reaction("◀")
        await message.add_reaction("▶")

    def gen_leaderboard_content(self, attribute, start, column):
        board = self.repo.get_leaderboard(attribute, start-1)
        guild = self.bot.get_guild(cfg.guild_id)

        output = ""
        for i, user in enumerate(board, start):
            username = guild.get_member(int(user.member_ID))
            if username is None:
                line = '{} – *User left*: {} pts\n'.format(i, getattr(user, column))
            else:
                username = disnake.utils.escape_markdown(username.display_name)
                line = '{} – **{}**: {} pts\n'.format(i, username, getattr(user, column))
            output += line

        return output

    def get_db_from_title(self, embed_title):
        if re.match(r".* GIVINGBOARD .*", embed_title):
            column = 'positive'
            attribute = Database_karma.positive.desc()
        elif re.match(r".* ISHABOARD .*", embed_title):
            column = 'negative'
            attribute = Database_karma.negative.desc()
        elif re.match(r".* LEADERBOARD .*", embed_title):
            column = 'karma'
            attribute = Database_karma.karma.desc()
        elif re.match(r".* BAJKARBOARD .*", embed_title):
            column = 'karma'
            attribute = Database_karma.karma
        else:
            return None
        max_page = self.repo.get_leaderboard_max()
        return column, attribute, max_page
