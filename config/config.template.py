class Config:

	def __init__(self):
		self.key = ""
		self.verification_role = ""
		self.admin_id = 0  # for mention in case of false verification
		self.connection = {
			'user': 'root',
			'password': '',
			'host': '127.0.0.1',
			'database': 'rubbergod',
			'port': '',
			'raise_on_warnings': True,
			'use_pure': False,
		}

	@staticmethod
	def info():
		info = '```====================\n RUBBERGOD COMMANDS \n====================\n'
		info = info + '!roll x y - Generates random integer from interval <x, y> \n'
		info = info + '!flip - Flips a coin \n'
		info = info + '!pick Is foo bar ? Yes No Maybe - Picks one of words after questionmark \n'
		info = info + '!karma - Returns your karma stats \n'
		info = info + '!leaderboard - Karma leaderboard \n'
		info = info + '!god - commandlist \n```'
		return info
