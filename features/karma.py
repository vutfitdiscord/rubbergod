import asyncio
from typing import List, Optional, Tuple, Union

import disnake
from disnake import Emoji
from disnake.ext.commands import Bot
from emoji import demojize

import utils
from cogs.grillbotapi import GrillbotApi
from config.app_config import config as cfg
from config.messages import Messages
from database.karma import KarmaDB, KarmaEmojiDB
from features.base_feature import BaseFeature


def test_emoji(db_emoji: bytearray, server_emoji: Emoji) -> bool:
    try:
        custom_emoji = int(db_emoji)
        return custom_emoji == server_emoji.id
    except ValueError:
        return False


def is_unicode(text: str) -> bool:
    demojized = demojize(text)
    if demojized.count(":") != 2:
        return False
    if demojized.split(":")[2] != "":
        return False
    return demojized != text


class Karma(BaseFeature):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.grillbot_api = GrillbotApi(bot)

    async def emoji_process_vote(
        self, inter: disnake.ApplicationCommandInteraction, emoji: Union[Emoji, str]
    ) -> Optional[int]:
        delay = cfg.vote_minutes * 60
        message = Messages.karma_vote_message(emote=str(emoji))
        message += Messages.karma_vote_info(delay=str(delay // 60), minimum=str(cfg.vote_minimum))
        message = await inter.channel.send(message)
        await inter.send(Messages.karma_revote_started)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        await message.add_reaction("0⃣")
        await asyncio.sleep(delay)

        message = await inter.channel.fetch_message(message.id)

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

    async def emoji_vote_value(self, inter: disnake.ApplicationCommandInteraction) -> None:
        emojis = KarmaEmojiDB.get_all_emojis()

        for server_emoji in inter.guild.emojis:
            if not server_emoji.animated:
                e = list(filter(lambda x: test_emoji(x.emoji_ID, server_emoji), emojis))

                if len(e) == 0:
                    KarmaEmojiDB.set_emoji_value(server_emoji, 0)
                    vote_value = await self.emoji_process_vote(inter, server_emoji)
                    emoji = server_emoji  # Save for use outside loop
                    break
        else:
            await inter.send(Messages.karma_vote_allvoted)
            return

        if vote_value is None:
            KarmaEmojiDB.remove_emoji(emoji)
            await inter.channel.send(
                Messages.karma_vote_notpassed(emote=str(emoji), minimum=str(cfg.vote_minimum))
            )

        else:
            KarmaEmojiDB.set_emoji_value(emoji, vote_value)
            await inter.channel.send(Messages.karma_vote_result(emote=str(emoji), result=str(vote_value)))

    async def emoji_revote_value(
        self, inter: disnake.ApplicationCommandInteraction, emoji: Union[Emoji, str]
    ) -> None:
        if not is_unicode(emoji):
            try:
                emoji_id = int(emoji.split(":")[2][:-1])
                emoji = await inter.guild.fetch_emoji(emoji_id)
            except (ValueError, IndexError):
                await inter.send(Messages.karma_revote_not_emoji)
                return
            except disnake.NotFound:
                await inter.send(Messages.emote_not_found(emote=emoji))
                return

        vote_value = await self.emoji_process_vote(inter, emoji)

        if vote_value is not None:
            KarmaEmojiDB.set_emoji_value(emoji, vote_value)
            await inter.channel.send(Messages.karma_vote_result(emote=str(emoji), result=str(vote_value)))
        else:
            await inter.channel.send(
                Messages.karma_vote_notpassed(emote=str(emoji), minimum=str(cfg.vote_minimum))
            )

    async def emoji_get_value(
        self, inter: disnake.ApplicationCommandInteraction, emoji: Union[Emoji, str], ephemeral: bool
    ) -> None:
        if not is_unicode(emoji):
            try:
                emoji_id = int(emoji.split(":")[2][:-1])
                emoji = await inter.channel.guild.fetch_emoji(emoji_id)
            except (ValueError, IndexError):
                await inter.response.send_message(Messages.karma_get_format)
                return
            except disnake.NotFound:
                await inter.response.send_message(Messages.emote_not_found(emote=emoji), ephemeral=ephemeral)
                return

        val = KarmaEmojiDB.emoji_value_raw(emoji)

        if val is not None:
            await inter.response.send_message(
                Messages.karma_get(emote=str(emoji), value=str(val)), ephemeral=ephemeral
            )
        else:
            await inter.response.send_message(
                Messages.karma_get_emote_not_voted(emote=str(emoji)), ephemeral=ephemeral
            )

    async def __make_emoji_list(self, guild: disnake.Guild, emojis: List[str]) -> Tuple[List[str], bool]:
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
                    KarmaEmojiDB.remove_emoji(emoji_id.decode())
                else:
                    KarmaEmojiDB.remove_emoji(str(emoji_id))

        message.append(line)
        message = [line for line in message if line != ""]
        return message, is_error

    async def emoji_list_all_values(
        self, inter: disnake.ApplicationCommandInteraction, ephemeral: bool
    ) -> None:
        error = False
        for value in ["1", "-1"]:
            emojis, is_error = await self.__make_emoji_list(
                inter.guild, KarmaEmojiDB.get_ids_of_emojis_valued(value)
            )
            error |= is_error
            try:
                await inter.followup.send(f"Hodnota {value}:", ephemeral=ephemeral)
                for line in emojis:
                    await inter.followup.send(line, ephemeral=ephemeral)
            except disnake.errors.HTTPException:
                pass  # TODO: error handling?

        if error:
            bot_dev_channel = await self.bot.fetch_channel(cfg.bot_dev_channel)
            await bot_dev_channel.send(Messages.karma_get_missing)

    async def karma_give(
        self, inter: disnake.ApplicationCommandInteraction, members: List[disnake.Member], karma: int
    ) -> None:
        members = await utils.get_members_from_tag(inter.guild, members)
        for member in members:
            KarmaDB.update_karma(member.id, inter.author.id, karma)
        if karma >= 0:
            await inter.send(
                Messages.karma_give_success(
                    user_list=" ".join([member.mention for member in members]), karma=karma
                )
            )
        else:
            await inter.send(
                Messages.karma_give_negative_success(
                    user_list=" ".join([member.mention for member in members]), karma=karma
                )
            )

    async def karma_transfer(
        self, inter: disnake.ApplicationCommandInteraction, from_user: disnake.User, to_user: disnake.User
    ) -> None:
        transfered = KarmaDB.transfer_karma(from_user.id, to_user.id)
        if transfered is None:
            await inter.send(Messages.karma_transer_user_no_karma(user=from_user))
            return

        formated_message = Messages.karma_transfer_complete(
            from_user=from_user.name,
            to_user=to_user.name,
            karma=transfered.karma,
            positive=transfered.positive,
            negative=transfered.negative,
        )
        await inter.send(formated_message)

    def karma_get(self, author: disnake.Member, target: Optional[disnake.Member] = None) -> str:
        if target is None:
            target = author
        k = KarmaDB.get_karma(target.id)
        return Messages.karma(
            user=author.id,
            karma=k.karma.value,
            order=k.karma.position,
            target=target.display_name,
            karma_pos=k.positive.value,
            karma_pos_order=k.positive.position,
            karma_neg=k.negative.value,
            karma_neg_order=k.negative.position,
        )

    async def message_karma(self, author: disnake.User, msg: disnake.Message) -> disnake.Embed:
        reactions = msg.reactions
        color = 0x6D6A69
        output = {"-1": [], "1": [], "0": []}
        karma = 0
        for react in reactions:
            emoji = react.emoji
            val = KarmaEmojiDB.emoji_value_raw(emoji)
            if val == 1:
                output["1"].append(emoji)
                karma += react.count
                async for user in react.users():
                    if user.id == msg.author.id:
                        karma -= 1
                        break
            elif val == -1:
                output["-1"].append(emoji)
                karma -= react.count
                async for user in react.users():
                    if user.id == msg.author.id:
                        karma += 1
                        break
            else:
                output["0"].append(emoji)
        embed = disnake.Embed(title="Karma zprávy")
        embed.add_field(name="Zpráva", value=msg.jump_url, inline=False)
        for key in ["1", "-1", "0"]:
            if output[key]:
                message = ""
                for emoji in output[key]:
                    message += str(emoji) + " "
                if key == "1":
                    name = "Pozitivní"
                elif key == "0":
                    name = "Neutrální"
                else:
                    name = "Negativní"
                embed.add_field(name=name, value=message, inline=False)
        if karma > 0:
            color = 0x34CB0B
        elif karma < 0:
            color = 0xCB410B
        embed.color = color
        embed.add_field(name="Celková karma za zprávu:", value=karma, inline=False)
        utils.add_author_footer(embed, author)
        return embed
