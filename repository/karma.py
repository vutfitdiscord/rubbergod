from repository.base_repository import BaseRepository
import mysql.connector
import asyncio
import discord


class Karma(BaseRepository):

    def __init__(self, client, utils):
        super().__init__()
        self.client = client
        self.utils = utils

    def valid_emoji(self, emoji_id):
        row = self.get_row("bot_karma_emoji", "emoji_id", emoji_id)
        return row[1] if row else 0

    def update_karma(self, member, emoji_value):
        db = mysql.connector.connect(**self.config.connection)
        cursor = db.cursor()
        if self.get_karma_value(member.id) is not None:
            cursor.execute('SELECT karma FROM bot_karma WHERE member_id = %s',
                           (member.id,))
            updated = cursor.fetchone()
            update = int(updated[0]) + emoji_value
            cursor.execute('UPDATE bot_karma SET karma = %s '
                           'WHERE member_id = %s',
                           (update, member.id))
        else:
            cursor.execute('INSERT INTO bot_karma (member_id, karma) '
                           'VALUES (%s, %s)',
                           (member.id, emoji_value))

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
        row = self.get_row("bot_karma", "member_id", member)
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
        delay = self.config.vote_minutes * 60
        message = await channel.send(
                 "{} {}\n"
                 "Hlasovani skonci za {} minut a minimalni pocet hlasu je: {}"
                 .format(self.config.vote_message, str(emote),
                         str(delay // 60), str(self.config.vote_minimum)))
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

        if plus + minus + neutral < self.config.vote_minimum:
            return None

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
                row = self.get_row("bot_karma_emoji", "emoji_id",
                                   emote.id)
                if row is None:
                    cursor.execute('INSERT INTO bot_karma_emoji '
                                   '(emoji_id, value) '
                                   'VALUES (%s, %s)',
                                   (emote.id, 0))
                    db.commit()
                    vote_value = await self.emote_vote(message.channel,
                                                       emote)
                    the_emote = emote
                    break
        else:
            db.close()
            await message.channel.send(
                    "Hlasovalo se jiz o kazdem emote")
            return

        if vote_value is None:
            cursor.execute('DELETE FROM bot_karma_emoji '
                           'WHERE emoji_id = %s',
                           (the_emote.id))

            await message.channel.send(
                    "Hlasovani o emotu {} neprošlo\n"
                    "Aspoň {} hlasů potřeba"
                    .format(str(the_emote), str(self.config.vote_minimum)))

            db.commit()
            db.close()
            return
        else:
            cursor.execute('UPDATE bot_karma_emoji SET value = %s '
                           'WHERE emoji_id = %s',
                           (vote_value, the_emote.id))
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

        vote_value = await self.emote_vote(message.channel, emote)

        if vote_value is not None:
            db = mysql.connector.connect(**self.config.connection)
            cursor = db.cursor()
            cursor.execute('INSERT INTO bot_karma_emoji (emoji_id, value) '
                           'VALUES (%s, %s) ON DUPLICATE KEY '
                           'UPDATE value = %s',
                           (emote.id, str(vote_value), str(vote_value)))
            db.commit()
            db.close()
        else:
            await message.channel.send(
                    "Hlasovani o emotu {} neprošlo\n"
                    "Aspoň {} hlasů potřeba"
                    .format(str(emote), str(self.config.vote_minimum)))
            return

        await message.channel.send(
                "Vysledek hlasovani o emotu {} je {}"
                .format(str(emote), str(vote_value)))
        return

    async def get(self, message):
        content = message.content.split()
        if len(content) != 3:
            return await self.get_all(message.channel)

        emote = content[2]
        try:
            emote_id = int(emote.split(':')[2][:-1])
        except (AttributeError, IndexError):
            await message.channel.send(
                    "Ocekavam pouze emote nebo nic")
            return

        try:
            emote = await message.channel.guild.fetch_emoji(emote_id)
        except discord.NotFound:
            await message.channel.send(
                    "Emote jsem na serveru nenasel")
            return

        row = self.get_row("bot_karma_emoji", "emoji_id", emote.id)
        await message.channel.send(
                "Hodnota {} : {}".format(str(emote),
                                         str(row[1] if row else None)))

    async def get_all(self, channel):
        for value in ["1", "-1"]:
            db = mysql.connector.connect(**self.config.connection)
            cursor = db.cursor()
            cursor.execute("SELECT * FROM bot_karma_emoji "
                           "WHERE value = %s", (value,))
            row = cursor.fetchall()
            db.close()
            await channel.send("Hodnota {}:".format(str(value)))

            message = ""
            for emote in row:
                if len(message) > 220:
                    await channel.send(message)
                    message = ""
                try:
                    emote = await channel.guild.fetch_emoji(emote[0])
                    message += str(emote)
                except discord.NotFound:
                    continue

            await channel.send(message)

    async def karma_give(self, message):
        input_string = message.content.split()
        if len(input_string) < 4:
            message.channel.send(
                "Toaster pls formát je !karma give NUMBER USER(s)")
        else:
            try:
                number = int(input_string[2])
            except ValueError:
                await message.channel.send("Čauec {} nie je číslo"
                                           .format(input_string[-1]))
                return
            for member in message.mentions:
                self.update_karma(member, number)
            if number >= 0:
                await message.channel.send("Karma bola úspešne pridaná")
            else:
                await message.channel.send("Karma bola úspešne odobraná")

    async def leaderboard(self, channel, order):
        board = self.get_leaderboard(order)
        i = 1
        if order == "DESC":
            output = "==================\n KARMA LEADERBOARD \n"
            output += "==================\n"
        else:
            output = "==================\n KARMA BAJKARBOARD \n"
            output += "==================\n"
        guild = self.client.get_guild(self.config.guild_id)
        for user in board:
            username = guild.get_member(int(user[0]))
            if username is None:
                continue
            username = str(username.name)
            line = '{} - {}:  {} pts\n'.format(i, username, user[1])
            output = output + line
            i = i + 1
        # '\n Full leaderboard - TO BE ADDED (SOON*tm*) \n'
        await channel.send(output)
