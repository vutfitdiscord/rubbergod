import utils
from repository.base_repository import BaseRepository

class Karma_row_data():
    def __init__(self, value, position):
        self.value = value
        self.position = position

class Karma_data():
    def __init__(self, karma, positive, negative):
        self.karma = karma
        self.positive = positive
        self.negative = negative

class KarmaRepository(BaseRepository):

    def __init__(self):
        super().__init__()

    def get_emojis_valued(self, val):
        """Returns a list of ids of emojis with specified value"""
        all_rows = self.get_all("bot_karma_emoji", "value", val)
        return [row[0] for row in all_rows]

    def get_all_emojis(self):
        """Returns a list of (emoji_id, value) tuples."""
        return self.get_all("bot_karma_emoji")

    def emoji_value(self, emoji_id):
        """Returns the value of an emoji.
        If the emoji has not been voted for, returns 0."""
        val = self.emoji_value_raw(emoji_id)
        return val if val is not None else 0

    def emoji_value_raw(self, emoji_id):
        """Returns the value of an emoji.
        If the emoji has not been voted for, returns None."""
        row = self.get_row("bot_karma_emoji", "emoji_id",
                           utils.str_emoji_id(emoji_id))
        return row[1] if row else None

    def set_emoji_value(self, emoji_id, value: int):
        cursor = self.cursor()
        cursor.execute('INSERT INTO bot_karma_emoji (emoji_id, value) '
                       'VALUES (%s, %s) ON DUPLICATE KEY '
                       'UPDATE value = %s',
                       (utils.str_emoji_id(emoji_id),
                        str(value), str(value)))
        self.db.commit()

    def remove_emoji(self, emoji_id):
        cursor = self.cursor()
        cursor.execute('DELETE FROM bot_karma_emoji '
                       'WHERE emoji_id = %s',
                       (utils.str_emoji_id(emoji_id),))
        self.db.commit()

    def update_karma(self, member, giver, emoji_value, remove=False):
        cursor = self.cursor()

        self.update_karma_get(cursor, member, emoji_value)
        self.update_karma_give(cursor, giver, emoji_value, remove)

        self.db.commit()

    def update_karma_get(self, cursor, member, emoji_value):
        if self.get_karma_value('bot_karma', member.id) is not None:
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

        self.db.commit()

    def update_karma_give(self, cursor, giver, emoji_value, remove):
        if emoji_value > 0:
            if remove:
                column = 'negative'
            else:
                column = 'positive'
        else:
            if remove:
                column = 'positive'
            else:
                column = 'negative'

        if column == 'negative':
            emoji_value *= -1

        if self.get_karma_value('bot_karma_giving', giver.id) is not None:
            cursor.execute('SELECT {} FROM bot_karma_giving '
                           'WHERE member_id = %s'.format(column),
                           (giver.id,))
            updated = cursor.fetchone()
            update = int(updated[0]) + emoji_value
            cursor.execute('UPDATE bot_karma_giving SET {} = %s '
                           'WHERE member_id = %s'.format(column),
                           (update, giver.id))
        else:
            if column == 'positive':
                cursor.execute('INSERT INTO bot_karma_giving '
                               '(member_id, positive, negative) '
                               'VALUES (%s, %s, %s)',
                               (giver.id, emoji_value, 0))
            else:
                cursor.execute('INSERT INTO bot_karma_giving '
                               '(member_id, positive, negative) '
                               'VALUES (%s, %s, %s)',
                               (giver.id, 0, emoji_value))
        self.db.commit()

    def karma_emoji(self, member_id, giver, emoji_id):
        emoji_value = int(self.emoji_value(str(emoji_id)))
        if emoji_value:
            self.update_karma(member_id, giver, emoji_value)

    def karma_emoji_remove(self, member_id, giver, emoji_id):
        emoji_value = int(self.emoji_value(str(emoji_id)))
        if emoji_value:
            self.update_karma(member_id, giver, emoji_value * (-1), True)

    def get_karma_value(self, database, member_id):
        row = self.get_row(database, "member_id", member_id)
        if database == 'bot_karma':
            return row[1] if row else None
        elif database == 'bot_karma_giving':
            return (row[1], row[2]) if row else None
        else:
            raise Exception('Nespravna databaze v get_karma_value')

    def get_karma_position(self, database, column, karma):
        cursor = self.cursor()
        cursor.execute("SELECT count(*) "
                       "FROM {} "
                       "WHERE {} > %s"
                       .format(database, column),
                       (str(karma),))
        row = cursor.fetchone()
        return row[0] + 1

    def get_karma(self, member_id):
        database = "bot_karma"
        giving_database = "bot_karma_giving"

        karma_value = self.get_karma_value(database, member_id)
        giving = self.get_karma_value(giving_database, member_id)        

        if karma_value is None:
            karma_value = 0

        order = self.get_karma_position(database, "karma", karma_value)

        if giving is None:
            pos_value = 0
            neg_value = 0
        else:
            pos_value = giving[0]
            neg_value = giving[1]

        pos_order = self.get_karma_position(giving_database, "positive", pos_value)
        neg_order = self.get_karma_position(giving_database, "negative", neg_value)

        karma = Karma_row_data(karma_value,order)
        positive = Karma_row_data(pos_value,pos_order)
        negative = Karma_row_data(neg_value,neg_order)

        result = Karma_data(karma,positive,negative)
        return result

    def get_leaderboard(self, database, column, order):
        cursor = self.cursor()
        cursor.execute("SELECT * FROM {} ORDER BY {} {} LIMIT 10"
                       .format(database, column, order))
        leaderboard = cursor.fetchall()
        return leaderboard
