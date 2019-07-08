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

        # Base bot behavior
        self.command_prefix = '!'

        # Roll dice
        self.max_dice_at_once = 1000
        self.dice_before_collation = 20
        self.max_dice_groups = 10
        self.max_dice_sides = 10000

        # Voting
        self.vote_minimum = 20
        self.vote_minutes = 2

        # Logging to discord
        self.log_channel_id = 0

        # String constants
        self.role_string = "Role"
        self.server_warning = "Tohle funguje jen na VUT FIT serveru"
        self.vote_room = 461544375105749003
        self.vote_message = "Hlasovani o karma ohodnoceni emotu"
        self.bot_room = 461549842896781312

        # Arcas
        self.arcas_id = 140547421733126145

        self.info = '```'\
                    '====================\n'\
                    ' RUBBERGOD COMMANDS \n'\
                    '====================\n'\
                    '!roll x y - \
                    Generates random integer from interval <x, y> \n'\
                    '!flip - Flips a coin \n'\
                    '!pick Is foo bar ? Yes No Maybe '\
                    '- Picks one of words after questionmark \n'\
                    '!karma - Returns your karma stats \n'\
                    '!karma get - \
                    Returns a list of all non-zero valued emotes \n'\
                    '!karma get *emote* - \
                    Returns the karma value of an emote \n'\
                    '!karma vote - \
                    Odstartuje hlasovani o hodnote zatim neohodnoceneho emotu \n'\
                    '!karma revote *emote* - \
                    Odstartuje hlasovani o nove hodnote emotu \n'\
                    '!leaderboard - Karma leaderboard \n'\
                    '!bajkarboard - Karma leaderboard reversed \n'\
                    '!diceroll - all kinds of dice rolling \n'\
                    '!god - commandlist \n'\
                    '```'
