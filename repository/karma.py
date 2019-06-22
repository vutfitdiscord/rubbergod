from repository.base_repository import BaseRepository
from repository import utils
import mysql.connector


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
