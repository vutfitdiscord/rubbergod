import sqlite3
from BaseModel import BaseModel


class Karma(BaseModel):

	def valid_emoji(self, emoji_id):
		row = self.get_row("bot_karma_emoji", "emoji_id = {}".format(emoji_id))
		return row[1] if row else 0

	def update_karma(self, member, emoji_value):
		db = sqlite3.connect('database.db')  # sqlite connection
		cursor = db.cursor()

		if self.get_karma(member.id):
			updated = cursor.execute('SELECT karma FROM bot_karma WHERE member_id = ?', [member.id]).fetchone()
			update = int(updated[0]) + emoji_value
			cursor.execute('UPDATE bot_karma SET karma = ? WHERE member_id = ?', (update, member.id))
		else:
			cursor.execute("INSERT INTO bot_karma (member_id, karma) VALUES (?,?)", (member.id, emoji_value))

		db.commit()
		db.close()

	def karma_emoji(self, member, emoji_id):
		emoji_value = self.valid_emoji(emoji_id)
		if emoji_value:
			self.update_karma(member, emoji_value)

	def karma_emoji_remove(self, member, emoji_id):
		emoji_value = self.valid_emoji(emoji_id)
		if emoji_value:
			self.update_karma(member, emoji_id*-1)

	def get_karma(self, user_id):
		row = self.get_row("bot_karma", "member_id = {}".format(user_id))
		return row[1] if row else 0

	def get_leaderboard(self):
		db = sqlite3.connect('database.db')  # sqlite connection
		cursor = db.cursor()
		row = cursor.execute('SELECT * FROM bot_karma ORDER BY karma DESC LIMIT 10').fetchall()
		db.close()
		return row
