class Config:

	def __init__(self):
		self.key = "NDA3NDQ2MTQyODg1MDM2MDMz.DlBGZQ.VJ34XvFMdYzwF_VhU6L9MlQWbI8"
		self.verification_role = "Verified"
		self.admin_id = 341875437410189315
		self.connection = {
			'user': 'rubberduck',
			'password': '5n#s6jVqgP6W0$!%f7L',
			'host': 'mariadb101.websupport.sk',
			'database': 'rubberduck',
			'port': '3312',
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
		info = info + '!leaderboard\n'
		info = info + '!god - commandlist \n```'
		return info
