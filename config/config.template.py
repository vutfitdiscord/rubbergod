class Config:
    key = ''
    verification_role = ''
    verification_role_id = 591349196267716608
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
    ignored_prefixes = ('!')

    # Extensions loaded on bot start
    extensions = ['base', 'karma', 'meme', 'random', 'verify', 'fitwide',
                  'acl', 'review', 'vote', 'kachna', 'name_day', "week", "weather"]

    # Roll dice
    max_dice_at_once = 1000
    dice_before_collation = 20
    max_dice_groups = 10
    max_dice_sides = 10000

    # Karma
    karma_ban_role_id = -1
    #                        add-roles         back-to-school
    karma_banned_channels = [591384273051975683, 622202824377237504]

    # Voting
    vote_minimum = 20
    vote_minutes = 2

    # Pin emoji count to pin
    pin_count = 20
    #                       skolni-info          server-info
    pin_banned_channels = [491277786489683979, 489461089432633346]

    # Special channel IDs
    log_channel = 531058805233156096
    bot_dev_channel = 597009137905303552
    vote_room = 461544375105749003
    bot_room = 461549842896781312
    mod_room = 505679727936143361

    allowed_channels = [
            bot_room,
            bot_dev_channel
    ]

    # String constants
    role_string = 'Role\n'
    #                add-roles         back-to-school        summertime-madness
    role_channels = [591384273051975683, 622202824377237504, 623290691774316574]
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

    # Subjects shortcuts
    subjects = [
        "ags", "alg", "ial", "iale", "ais", "ian", "mba", "ja3", "ja3", "ban1",
        "ban2", "ban3", "ban3", "ban4", "ban4", "ja6d", "aeu", "aeu", "ait",
        "ait", "fce", "pdd", "evo", "iach", "avs", "ata", "ibp", "ibt", "ibte",
        "baya", "bms", "bza", "ibs", "bis", "bid", "bif", "iv108", "bin",
        "bio", "csoa", "icuz", "icul", "czsa", "ids", "idse", "ds_2p", "fit",
        "idf1", "idf2", "iddl", "iddz", "iw1", "c3p", "dfaa", "dip", "dipa",
        "dipe", "idm", "dja", "eip", "iel", "eud", "evd", "fik", "ifan",
        "fad", "ifj", "ifje", "flp", "fvs", "ifai", "ifea", "fyo", "fyoe",
        "ifs", "gzn", "gja", "gjae", "gux", "gmu", "gal", "gale", "hsc",
        "hsce", "iis", "ivg", "isd", "sin", "wap", "iipd", "iipd", "ijc",
        "krd", "kko", "knn", "kry", "ikpt", "ikpt", "ilg", "sla", "log",
        "imae", "mpr", "hko", "hko", "hvr", "hvr", "ima1", "mld", "mat",
        "mate", "imf", "ism", "mmat", "imk", "imie", "imp", "impe", "ims",
        "msd", "mid", "mmd", "mzd", "tid", "mtia", "mog", "mul", "mule",
        "imu", "ini", "inc", "ince", "cpsa", "inp", "nav", "nsb", "inm",
        "ios", "opd", "opm", "dpc-tk1", "orid", "prl", "pcg", "ipso", "ipso",
        "ipz", "ipze", "pgd", "pgr", "pgre", "ippk", "ipk", "ipke", "pova",
        "isc", "ipma", "pbi", "iam", "pgpa", "ili", "ipa", "pbd", "pcs",
        "pdb", "pdbe", "pis", "pks", "pos", "pnd", "ccs", "ivs", "ppp", "prm",
        "prm", "pds", "pdse", "toi", "ipp", "ippe", "ptd", "ips", "isu",
        "iw5", "iza", "ip1", "pp1", "ip1e", "ip1e", "pp1e", "pp1e", "ip2",
        "pp2", "ip2e", "ip3", "pma", "pdi", "rgd", "ret", "ret", "roba",
        "isp", "itt", "sep", "sepa", "itte", "sepe", "ics", "icp", "ija",
        "ijae", "smt", "ivh", "sem", "iw2", "iss", "snt", "c2p", "i1c", "isa",
        "iw3", "isj", "sloa", "sfc", "js1", "js1", "iiz", "sav", "msp", "dma1",
        "ssp", "sri", "sur", "sod", "spp", "rtsa", "itp", "i2c", "tin", "tine",
        "tad", "pftd", "the", "tkd", "tjd", "its", "tama", "itu", "itue",
        "itw", "itwe", "ity", "iuce", "upa", "sui", "iumi", "ius", "uxia",
        "vdd", "viza", "apd", "vkd", "ivp1", "ivp2", "vpd", "sid", "zzd",
        "vyf", "vge", "vgee", "vnd", "vnv", "vnve", "vypa", "vin", "zpx",
        "zpx", "izep", "izfi", "zha", "izma", "izg", "izp", "izu", "izue",
        "zzn", "jad", "jad", "izsl", "zpo", "zpoe", "zpd", "zpja", "asd",
        "zre", "zree"
    ]
    #                            MUNI                Host
    reviews_forbidden_roles = [600047283509264384, 603673568051462144]

    # How many people to print if the limit argument is not specified
    rolehoarder_default_limit = 10

    # Arcas
    arcas_id = 140547421733126145
    arcas_delay = 24

    # uh oh
    uhoh_string = 'uh oh'

    # grillbot
    grillbot_id = 0

    # kachna countdown
    kachna_open_hour = 16
    kachna_close_hour = 22
    kachna_open_days = [0, 2] # 0 = Monday, 1=Tuesday, 2=Wednesday...
    kachna_temp_closed = False

    # name day source url
    name_day_url_cz = "http://svatky.adresa.info/json"
    name_day_url_sk = "http://svatky.adresa.info/json?lang=sk"

    # weather token to openweather API
    weather_token = "678a5932f6dd92ac668b20e9f89c0318"

    # Warphole config
    warphole_blue = 0
    warphole_orange = 0

    # warden
    duplicate_limit = 5
    #                           #memes              #aww
    deduplication_channels = [461548323116154880, 543083844736253964]

    # week command
    starting_week = 5
