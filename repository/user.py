from repository.base_repository import BaseRepository


class User(BaseRepository):

	def save_record(self, message):
		""""Inserts login with discord name into database"""
		login = str(message.content).split(" ", 1)[1]  # gets login from command
		cursor = self.db.cursor()
		insert = cursor.execute('INSERT INTO bot_permit (login, discord_name) VALUES ("{}", "{}")'.format(login, str(message.author)))
		self.db.commit()
		return insert

	@staticmethod
	def has_role(message, role):
		""""Checks if user has defined role"""
		has_role = False
		for user_role in message.author.roles:
			if str(user_role) == role:
				has_role = True
		return has_role

	def find_login(self, message):
		""""Finds login from database"""
		login = str(message.content).split(" ", 1)[1] # gets login from command
		cursor = self.db.cursor()
		cursor.execute('SELECT * FROM bot_valid_persons WHERE `login`="{}" AND status = 1'.format(login))
		return cursor.fetchone()
