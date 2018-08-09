from BaseModel import BaseModel
import sqlite3

class User(BaseModel):

	def has_role(self, message, role):
		""""Checks if user has defined role"""
		has_role = False
		for user_role in message.author.roles:
			if str(user_role) == role:
				has_role = True
		return has_role

	def find_login(self, message):
		""""Finds login from database"""
		login = str(message.content).split(" ", 1)[1] # gets login from command
		db = sqlite3.connect('database.db') # sqlite connection
		cursor = db.cursor()
		row = cursor.execute('SELECT * FROM bot_valid_persons WHERE login = ? AND status = 1', [login]).fetchone() # finds login in database
		db.close()
		return row