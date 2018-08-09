import sqlite3
import model


def valid_emoji(emojiId):
	row = model.get_row("bot_karma_emoji", "emoji_id = {}".format(emojiId))
	return row[1] if row else 0


def update_karma(member, emojiValue):
	db = sqlite3.connect('database.db') # sqlite connection
	cursor = db.cursor()

	if get_karma(member.id):
		updated = cursor.execute('SELECT karma FROM bot_karma WHERE member_id = ?', [member.id]).fetchone()
		update = int(updated[0]) + emojiValue
		cursor.execute('UPDATE bot_karma SET karma = ? WHERE member_id = ?', (update, member.id))
	else:
		cursor.execute("INSERT INTO bot_karma (member_id, karma) VALUES (?,?)", (member.id, emojiValue))

	db.commit()
	db.close()


def karma_emoji(member, emojiId):
	emojiValue = valid_emoji(emojiId)
	if emojiValue:
		update_karma(member, emojiValue)


def karma_emoji_remove(member, emojiId):
	emojiValue = valid_emoji(emojiId)
	if emojiValue:
		update_karma(member, emojiValue*-1)


def get_karma(userId):
	row = model.get_row("bot_karma", "member_id = {}".format(userId))
	return row[1] if row else 0


def get_leaderboard():
	db = sqlite3.connect('database.db') # sqlite connection
	cursor = db.cursor()
	row = cursor.execute('SELECT * FROM bot_karma ORDER BY karma DESC LIMIT 10').fetchall()
	db.close()
	return row
