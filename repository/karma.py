from repository.base_repository import BaseRepository
import mysql.connector


class Karma(BaseRepository):

	def valid_emoji(self, emoji_id):
		row = self.get_row("bot_karma_emoji", "emoji_id = {}".format(emoji_id))
		return row[1] if row else 0

	def update_karma(self, member, emoji_value):
		db = mysql.connector.connect(**self.config.connection)
		cursor = db.cursor()
		if self.get_karma(member.id):
			cursor.execute('SELECT karma FROM bot_karma WHERE member_id = "{}"'.format(member.id))
			updated = cursor.fetchone()
			update = int(updated[0]) + emoji_value
			cursor.execute('UPDATE bot_karma SET karma = "{}" WHERE member_id = "{}"'.format(update, member.id))
		else:
			cursor.execute('INSERT INTO bot_karma (member_id, karma) VALUES ("{}","{}")'.format(member.id, emoji_value))

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

	def get_karma(self, user_id):
		row = self.get_row("bot_karma", "member_id = {}".format(user_id))
		return row[1] if row else 0

	def get_leaderboard(self):
		db = mysql.connector.connect(**self.config.connection)
		cursor = db.cursor()
		cursor.execute('SELECT * FROM bot_karma ORDER BY karma DESC LIMIT 10')
		leaderboard = cursor.fetchall()
		db.close()
		return leaderboard
