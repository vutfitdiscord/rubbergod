class Config:

    def __init__(self):
        self.key = ""
        self.verification_role = ""
        self.admin_id = 0   # for mention in case of false verification
        self.guild_id = 0
        self.email_pass = ""
        # So that you can verify in PMs this is the server you get the roles at
        self.connection = {
            'user': 'root',
            'password': '',
            'host': '127.0.0.1',
            'database': 'rubbergod',
            'port': '',
            'raise_on_warnings': True,
            'use_pure': False,
        }

        # Roll dice
        self.max_dice_at_once = 1000
        self.dice_before_collation = 20
        self.max_dice_groups = 10
        self.max_dice_sides = 10000

    @staticmethod
    def info():
        info = '```'\
               '====================\n'\
               ' RUBBERGOD COMMANDS \n'\
               '====================\n'\
               '!roll x y - Generates random integer from interval <x, y> \n'\
               '!flip - Flips a coin \n'\
               '!pick Is foo bar ? Yes No Maybe '\
               '- Picks one of words after questionmark \n'\
               '!karma - Returns your karma stats \n'\
               '!leaderboard - Karma leaderboard \n'\
               '!god - commandlist \n'\
               '```'
        return info
