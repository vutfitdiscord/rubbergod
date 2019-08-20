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
    db_string = "postgres://postgres:postgres@db:5432/postgres"

    # Base bot behavior
    command_prefix = ('?', '!')
    default_prefix = '?'

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

    # Pin emoji count to pin
    pin_count = 20

    # Special channel IDs
    log_channel = 531058805233156096
    bot_dev_channel = 597009137905303552
    vote_room = 461544375105749003
    bot_room = 461549842896781312

    allowed_channels = [
            bot_room,
            bot_dev_channel
    ]

    # String constants
    role_string = 'Role'
    hug_emojis = ["<:peepoHug:600435649786544151>",
                  "<:peepoHugger:602052621007585280>",
                  "<:huggers:602823825880514561>", "(っ˘̩╭╮˘̩)っ", "(っ´▽｀)っ",
                  "╰(*´︶`*)╯", "(つ≧▽≦)つ", "(づ￣ ³￣)づ", "(づ｡◕‿‿◕｡)づ",
                  "(づ￣ ³￣)づ", "(っ˘̩╭╮˘̩)っ", "⁽₍੭ ՞̑◞ළ̫̉◟՞̑₎⁾੭",
                  "(੭ु｡╹▿╹｡)੭ु⁾⁾", "(*´σЗ`)σ", "(っ´▽｀)っ", "(っ´∀｀)っ",
                  "c⌒っ╹v╹ )っ", "(σ･з･)σ", "(੭ु´･ω･`)੭ु⁾⁾", "(oﾟ▽ﾟ)o",
                  "༼つ ் ▽ ் ༽つ", "༼つ . •́ _ʖ •̀ . ༽つ", "╏つ ͜ಠ ‸ ͜ಠ ╏つ",
                  "༼ つ ̥◕͙_̙◕͖ ͓༽つ", "༼ つ ◕o◕ ༽つ", "༼ つ ͡ ͡° ͜ ʖ ͡ ͡° ༽つ",
                  "(っಠ‿ಠ)っ", "༼ つ ◕_◕ ༽つ", "ʕっ•ᴥ•ʔっ", "", "༼ つ ▀̿_▀̿ ༽つ",
                  "ʕ ⊃･ ◡ ･ ʔ⊃", "╏つ” ⊡ 〜 ⊡ ” ╏つ", "(⊃｡•́‿•̀｡)⊃", "(っ⇀⑃↼)っ",
                  "(.づ◡﹏◡)づ.", "(.づσ▿σ)づ.", "(っ⇀`皿′↼)っ",
                  "(.づ▣ ͜ʖ▣)づ.", "(つ ͡° ͜ʖ ͡°)つ", "(⊃ • ʖ̫ • )⊃",
                  "（っ・∀・）っ", "(つ´∀｀)つ", "(っ*´∀｀*)っ", "(つ▀¯▀)つ",
                  "(つ◉益◉)つ", " ^_^ )>", "───==≡≡ΣΣ((( つºل͜º)つ",
                  "─=≡Σ((( つ◕ل͜◕)つ", "─=≡Σ((( つ ◕o◕ )つ",
                  "～～～～(/￣ｰ(･･｡)/", "───==≡≡ΣΣ(づ￣ ³￣)づ",
                  "─=≡Σʕっ•ᴥ•ʔっ", "───==≡≡ΣΣ(> ^_^ )>", "─=≡Σ༼ つ ▀̿_▀̿ ༽つ",
                  "───==≡≡ΣΣ(っ´▽｀)っ", "───==≡≡ΣΣ(っ´∀｀)っ", "～～(つˆДˆ)つﾉ>｡☆)ﾉ"]

    # Arcas
    arcas_id = 140547421733126145
    arcas_delay = 24


    # uh oh
    uhoh_string = 'uh oh'
