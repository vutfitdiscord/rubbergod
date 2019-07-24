class Config:
    key = ''
    verification_role = ''
    admin_id = 0  # for mention in case of false verification
    guild_id = 0

    # Verification email sender settings
    email_name = 'toasterrubbergod@gmail.com'
    email_addr = 'toasterrubbergod@gmail.com'
    email_smtp_server = 'smtp.gmail.com'
    email_smtp_port = 465
    email_pass = ''

    # Database
    connection = {
        'user': 'root',
        'password': '',
        'host': '127.0.0.1',
        'database': 'rubbergod',
        'port': '',
        'raise_on_warnings': True,
        'use_pure': False,
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
    }

    # Base bot behavior
    command_prefix = '!'

    # Roll dice
    max_dice_at_once = 1000
    dice_before_collation = 20
    max_dice_groups = 10
    max_dice_sides = 10000

    # Karma
    karma_ban_role_id = -1
    karma_banned_channels = []

    # Voting
    vote_minimum = 20
    vote_minutes = 2

    # Special channel IDs
    log_channel_id = 597009137905303552
    vote_room = 461544375105749003
    bot_room = 461549842896781312

    # String constants
    role_string = 'Role'

    # Arcas
    arcas_id = 140547421733126145