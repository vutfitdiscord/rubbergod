import sqlite3
from random import randint


def get_row(table, where):
	db = sqlite3.connect('database.db')  # sqlite connection
	cursor = db.cursor()
	row = cursor.execute('SELECT * FROM {} WHERE {}'.format(table, where)).fetchone()
	db.close()
	return row


def has_role(message, role):
	""""Checks if user has defined role"""
	has_role = False
	for user_role in message.author.roles:
		if str(user_role) == role:
			has_role = True
	return has_role


def find_login(message):
	""""Finds login from database"""
	login = str(message.content).split(" ", 1)[1] # gets login from command
	db = sqlite3.connect('database.db') # sqlite connection
	cursor = db.cursor()
	row = cursor.execute('SELECT * FROM bot_valid_persons WHERE login = ? AND status = 1', [login]).fetchone() # finds login in database
	db.close()
	return row


def save_record(message):
	""""Inserts login with discord name into database"""
	login = str(message.content).split(" ", 1)[1] # gets login from command
	db = sqlite3.connect('database.db') # sqlite connection
	cursor = db.cursor()
	insert = cursor.execute("INSERT INTO bot_permit (login, discord_name) VALUES (?,?)", (login, str(message.author)))
	db.commit()
	db.close()
	return insert


def pick_option(message):
	""""Pick one option from message"""
	split = message.content.split()
	if len(split) > 2:
		if "?" in split:
			separatorIndex = split.index("?")
			if separatorIndex:
				if ((len(split) - 1) - (separatorIndex + 1)) > 0:
					return split[randint(separatorIndex + 1, len(split) - 1)]
		else:
			return split[randint(1, len(split) - 1)]
	return False


def generate_number(message):
	""""Generate random number from interval"""
	string = message.content.split(" ")
	x = int(string[1])
	y = int(string[2])
	if x > y:
		x, y = y, x  # variable values swap
	return randint(x, y)


def flip():
	return "True" if randint(0, 1) else "False"


def info():
	info = '```====================\n RUBBERGOD COMMANDS \n====================\n'
	info = info + '!roll x y - Generates random integer from interval <x, y> \n'
	info = info + '!flip - Flips a coin \n'
	info = info + '!pick Is foo bar ? Yes No Maybe - Picks one of words after questionmark \n'
	info = info + '!karma - Returns your karma stats \n'
	info = info + '!leaderboard - Karma leaderboard \n'
	info = info + '!god - commandlist \n```'
	return info


def deadlines():
	db = sqlite3.connect('database.db') # sqlite connection
	cursor = db.cursor()
	rows = cursor.execute('SELECT * FROM bot_actuality').fetchall()
	db.close()
	line = ""
	for actuality in rows:
		nline = '**' + str(actuality[2])  + '** - ' + str(actuality[1]) + ' - ' + actuality[3] + ' - ' + str(actuality[4]) + '\n'
		if len(nline + line) <= 2000:
			line = line + nline
	return line
