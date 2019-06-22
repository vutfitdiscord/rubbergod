from repository.base_repository import BaseRepository
from repository import utils
import mysql.connector
import asyncio
import discord


class Karma(BaseRepository):

    utils = utils.Utils()

    def valid_emoji(self, emoji_id):
        row = self.get_row("bot_karma_emoji", "emoji_id = {}".format(emoji_id))
        return row[1] if row else 0

    def update_karma(self, member, emoji_value):
        db = mysql.connector.connect(**self.config.connection)
        cursor = db.cursor()
        if self.get_karma_value(member.id) is not None:
            cursor.execute('SELECT karma FROM bot_karma WHERE member_id = "{}"'
                           .format(member.id))
            updated = cursor.fetchone()
            update = int(updated[0]) + emoji_value
            cursor.execute('UPDATE bot_karma SET karma = "{}" '
                           'WHERE member_id = "{}"'
                           .format(update, member.id))
        else:
            cursor.execute('INSERT INTO bot_karma (member_id, karma) '
                           'VALUES ("{}","{}")'
                           .format(member.id, emoji_value))

        db.commit()
        db.close()

    def karma_emoji(self, member, emoji_id):
        emoji_value = self.valid_emoji(emoji_id)
        if emoji_value:
            self.update_karma(member, emoji_value)

    def karma_emoji_remove(self, member, emoji_id):
        emoji_value = int(self.valid_emoji(emoji_id))
        if emoji_value:
            self.update_karma(member, emoji_value * (-1))

    def get_karma_value(self, member):
        row = self.get_row("bot_karma", "member_id = {}".format(member))
        return row[1] if row else None

    def get_karma(self, member):
        karma = self.get_karma_value(member)
        if karma is None:
            karma = 0
        return ("Hey {}, your karma is: {}."
                .format(self.utils.generate_mention(member),
                        str(karma)))

    def get_leaderboard(self, order):
        db = mysql.connector.connect(**self.config.connection)
        cursor = db.cursor()
        cursor.execute('SELECT * FROM bot_karma ORDER BY karma ' + order +
                       ' LIMIT 10')
        leaderboard = cursor.fetchall()
        db.close()
        return leaderboard

    async def emote_vote(self, channel, emote):
        delay = 60 * 60
        message = await channel.send(
                ("Hlasovani o karma ohodnoceni emotu {}\n" +
                 "Hlasovani skonci za {} minut"
                 ).format(str(emote), str(delay // 60)))
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        await message.add_reaction("0⃣")
        await asyncio.sleep(delay)

        message = await channel.fetch_message(message.id)

        for reaction in message.reactions:
            if reaction.emoji == "✅":
                plus = reaction.count - 1
            elif reaction.emoji == "❌":
                minus = reaction.count - 1
            elif reaction.emoji == "0⃣":
                neutral = reaction.count - 1

        if plus > minus + neutral:
            return 1
        elif minus > plus + neutral:
            return -1
        else:
            return 0

    async def vote(self, message):
        if len(message.content.split()) != 2:
            await message.channel.send(
                    "Neocekavam argument")
            return
        db = mysql.connector.connect(**self.config.connection)
        cursor = db.cursor()
        cursor.execute('SELECT emoji_id FROM bot_karma_emoji')
        emotes = cursor.fetchall()

        guild = message.channel.guild
        vote_value = 0
        the_emote = None
        id_array = []
        for emote in emotes:
            id_array.append(emote[0])
        for emote in guild.emojis:
            if not emote.animated:
                if self.get_row("bot_karma_emoji", "emoji_id = {}".format(emote.id)) is None:
                    vote_value = await self.emote_vote(message.channel, emote)
                    the_emote = emote
                    break
        else:
            db.close()
            await message.channel.send(
                    "Hlasovalo se jiz o kazdem emote")
            return

        cursor.close()
        cursor = db.cursor()
        result = cursor.execute('INSERT INTO bot_karma_emoji (emoji_id, value)'
                                ' VALUES ("{}", "{}")'
                                .format(the_emote.id, vote_value))
        print(result)
        db.commit()
        db.close()
        await message.channel.send(
                "Vysledek hlasovani o emotu {} je {}"
                .format(str(the_emote), str(vote_value)))
        return

    async def revote(self, message):
        content = message.content.split()
        if len(content) != 3:
            await message.channel.send(
                    "Ocekavam pouze emote")
            return

        emote = content[2]
        try:
            emote_id = int(emote.split(':')[2][:-1])
        except (AttributeError, IndexError):
            await message.channel.send(
                    "Ocekavam pouze **emote**")
            return

        try:
            emote = await message.channel.guild.fetch_emoji(emote_id)
        except discord.NotFound:
            await message.channel.send(
                    "Emote jsem na serveru nenasel")
            return

        db = mysql.connector.connect(**self.config.connection)
        cursor = db.cursor()
        cursor.execute('SELECT emoji_id FROM bot_karma_emoji')
        emotes = cursor.fetchall()

        vote_value = await self.emote_vote(message.channel, emote)

        cursor.close()
        cursor = db.cursor()
        if emote.id not in emotes:
            cursor.execute('INSERT INTO bot_karma_emoji (emoji_id, value) '
                           'VALUES ("{}", "{}")'
                           .format(emote.id, str(vote_value)))
        else:
            cursor.execute('UPDATE bot_karma_emoji SET value = "{}" '
                           'WHERE emoji_id = "{}"'
                           .format(str(vote_value), emote.id))
        db.commit()
        db.close()
        await message.channel.send(
                "Vysledek hlasovani o emotu {} je {}"
                .format(str(emote), str(vote_value)))
        return

    async def get(self, message):
        content = message.content.split()
        if len(content) != 3:
            await message.channel.send(
                    "Ocekavam pouze emote")
            return

        emote = content[2]
        try:
            emote_id = int(emote.split(':')[2][:-1])
        except (AttributeError, IndexError):
            await message.channel.send(
                    "Ocekavam pouze **emote**")
            return

        try:
            emote = await message.channel.guild.fetch_emoji(emote_id)
        except discord.NotFound:
            await message.channel.send(
                    "Emote jsem na serveru nenasel")
            return

        row = self.get_row("bot_karma_emoji", "emoji_id = {}".format(emote.id))
        await message.channel.send(
                "Hodnota {} : {}".format(str(emote), str(row[1] if row else None)))
