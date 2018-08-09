import sqlite3


class BaseModel:

	def get_row(self, table, where):
		db = sqlite3.connect('database.db')  # sqlite connection
		cursor = db.cursor()
		row = cursor.execute('SELECT * FROM {} WHERE {}'.format(table, where)).fetchone()
		db.close()
		return row

	def save_record(self, message):
		""""Inserts login with discord name into database"""
		login = str(message.content).split(" ", 1)[1] # gets login from command
		db = sqlite3.connect('database.db') # sqlite connection
		cursor = db.cursor()
		insert = cursor.execute("INSERT INTO bot_permit (login, discord_name) VALUES (?,?)", (login, str(message.author)))
		db.commit()
		db.close()
		return insert

	def info(self):
		info = '```====================\n RUBBERGOD COMMANDS \n====================\n'
		info = info + '!roll x y - Generates random integer from interval <x, y> \n'
		info = info + '!flip - Flips a coin \n'
		info = info + '!pick Is foo bar ? Yes No Maybe - Picks one of words after questionmark \n'
		info = info + '!karma - Returns your karma stats \n'
		info = info + '!leaderboard - Karma leaderboard \n'
		info = info + '!god - commandlist \n```'
		return info
