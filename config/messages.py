from config import config


class Messages:
    prefix = config.Config.default_prefix

    server_warning = "Tohle funguje jen na VUT FIT serveru."
    toaster_pls = "Toaster pls, máš bordel v DB."
    missing_perms = "Na tohle nemas prava. {user}"
    acl_help = "{user}, Pouziti:\n`!acl {{action}} {{table}} [args]`\n"\
               "action: add, edit, del nebo list\n"\
               "table: group, rule, role nebo user\n"\
               "args zalezi na zvolene akci a tabulce, napriklad kdyz chcete"\
               "pridat groupu, musite zadat nazev groupy a nepovinne take "\
               "ID rodice jako argumnet"  # TODO: Correct to proper czech
    acl_add_group = "Group vytvorena."
    acl_edit_group = "Group zmenena."
    acl_del_group = "Group smazana."
    acl_add_rule = "Pravidlo vytvoreno."
    acl_edit_rule = "Pravidlo zmeneno."
    acl_del_rule = "Pravidlo smazano."
    acl_add_role = "Vyjimka pro roli pridana."
    acl_edit_role = "Vyjimka pro roli upravena."
    acl_del_role = "Vyjimka pro roli smazana."
    acl_add_user = "Vyjimka pro uzivatele pridana."
    acl_edit_user = "Vyjimka pro uzivatele upravena."
    acl_del_user = "Vyjimka pro uzivatele smazana."
    no_such_command = "Takový příkaz neznám. <:sadcat:576171980118687754>"
    spamming = "{user} Nespamuj tolik <:sadcat:576171980118687754>"
    insufficient_rights = "{user}, na použití tohoto příkazu nemáš právo."
    vote_room_only = "Tohle funguje jen v {room}."
    bot_room_redirect = "{} <:sadcat:576171980118687754> 👉 " \
                        "<#{}>\n"
    message_link_prefix = 'https://discordapp.com/channels/' \
                          + str(config.Config.guild_id) + '/'

    uhoh_counter = "{uhohs} uh ohs od spuštění."
    uptime_message = "Up since:  `{boottime}`\nUptime:\t`{uptime}`"

    karma = "{user} Karma uzivatele `{target}` je: **{karma}** " \
            "(**{order}.**)\nA rozdal:\n" \
            "**{karma_pos}** pozitivní karmy " \
            "(**{karma_pos_order}.**)\n" \
            "**{karma_neg}** negativní karmy " \
            "(**{karma_neg_order}.**)"

    karma_invalid_command = "Neznámý karma příkaz."
    karma_vote_format = "Neočekávám argument. " \
                        "Správný formát: `" + prefix + "karma vote`"
    karma_vote_message_hack = "Hlasování o karma ohodnocení emotu"
    karma_vote_message = karma_vote_message_hack + " {emote}"
    karma_vote_info = "Hlasování skončí za **{delay}** " \
                      "minut a minimální počet hlasů je " \
                      "**{minimum}**."
    karma_vote_result = "Výsledek hlasování o emotu {emote} " \
                        "je {result}."
    karma_vote_notpassed = "Hlasovani o emotu {emote} neprošlo\n" \
                           "Aspoň {minimum} hlasů potřeba."
    karma_vote_allvoted = "Už se hlasovalo o všech emotech."
    karma_revote_format = "Očekávám pouze formát: " \
                          "`" + prefix + "karma revote [emote]`"
    karma_emote_not_found = "Emote jsem na serveru nenašel."
    karma_get_format = "Použití:\n" \
                       "`" + prefix + "karma get`: " \
                       "vypíše všechny emoty s hodnotou.\n" \
                       "`" + prefix + "karma get [emote]`: " \
                       "vrátí hodnotu daného emotu."
    karma_get = "Hodnota {emote} je {value}."
    karma_get_emote_not_voted = "{emote} není ohodnocen."
    karma_give_format = "Toaster pls, formát je " \
                        "`" + prefix + "karma give [number] [user(s)]`"
    karma_give_format_number = "Toaster pls, formát je " \
                               "`" + prefix + "karma give " \
                               "[number, jakože číslo, " \
                               "ne {input}] [user(s)]` "
    karma_give_success = "Karma byla úspěšně přidaná."
    karma_give_negative_success = "Karma byla úspěšně odebraná."
    member_not_found = "{user} Nikoho takového jsem nenašel."

    role_add_denied = "{user}, na přidání role {role} nemáš právo."
    role_remove_denied = "{user}, " \
                         "na odebrání role {role} nemáš právo."
    role_invalid_line = "{user}, řádek `{line}` je neplatný."
    role_format = "{user}, použij `!god`."
    role_not_on_server = "Nepíšeš na serveru, " \
                         "takže předpokládám, " \
                         "že myslíš role VUT FIT serveru."
    role_not_role = "{user}, {not_role} není role."
    role_invalid_emote = "{user}, {not_emote} " \
                         "pro roli {role} není emote."

    rng_generator_format = "Použití: `" + prefix + "roll x [y]`\n" \
                           "x, y je rozmezí čísel,\n" \
                           "x, y jsou celá čísla,\n" \
                           "pokud y není specifikováno, " \
                           "je považováno za 0."
    rng_generator_format_number = "{user}, zadej dvě celá čísla, " \
                                  "**integers**."

    rd_too_many_dice_in_group = "Příliš moc kostek v jedné " \
                                "skupině, maximum je {maximum}."
    rd_too_many_dice_sides = "Příliš moc stěn na kostkách, " \
                             "maximum je {maximum}."
    rd_too_many_dice_groups = "Příliš moc skupin kostek, " \
                              "maximum je {maximum}."
    rd_format = "Chybná syntax hodu ve skupině {group}."
    rd_help = "Formát naleznete na " \
              "https://wiki.roll20.net/Dice_Reference\n" \
              "Implementovány featury podle obsahu: **8. Drop/Keep**"

    verify_already_verified = "{user} Už jsi byl verifikován " \
                              "({toaster} pls)."
    verify_send_format = "Očekávám jeden argument. " \
                         "Správný formát: " \
                         "`" + prefix + "getcode [FIT login, " \
                         "ve tvaru xlogin00, nebo MUNI UCO]`"
    verify_send_dumbshit = "{user} Tvůj login. {emote}"
    verify_send_success = "{user} Kód byl odeslán na tvůj mail " \
                          "({mail})!\n" \
                          "Pro verifikaci použij: " \
                          "`" + prefix + "verify [login] [kód]`"
    verify_send_not_found = "{user} Login nenalezen " \
                            "nebo jsi už tímhle krokem " \
                            "prošel ({toaster} pls)."
    verify_verify_format = "Očekávám dva argumenty. " \
                           "Správný formát: " \
                           "`" + prefix + "verify [FIT login nebo " \
                           "MUNI UCO] [kód]`\n" \
                           "Pro získání kódu použij `" +\
                           prefix + "getcode [FIT login, ve tvaru " \
                           "xlogin00, nebo MUNI UCO]`"
    verify_verify_dumbshit = "{user} Kód, " \
                             "který ti přišel na mail. {emote}"
    verify_verify_manual = "Čauec {user}, nechám {toaster}, " \
                           "aby to udělal manuálně, " \
                           "jsi shady (Year: {year})"
    verify_verify_success = "{user} Gratuluji, byl jsi verifikován!"
    verify_post_verify_info = "Channely dobre navstivit po verifikaci:\n" \
                              "<#591384273051975683> Pro pridani roli\n" \
                              "<#489461089432633346> Pro pravidla " \
                              "a dalsi info"

    verify_verify_not_found = "{user} Login nenalezen nebo " \
                              "jsi už tímhle krokem prošel " \
                              "({toaster} pls)."
    verify_verify_wrong_code = "{user} Špatný kód."

    vote_format = "Použití vote:\n`" + prefix + "vote [otázka]\n[emoji] [odpověď 1]\n[emoji] [odpověď 2]\na tak dále`"
    vote_not_emoji = "{not_emoji} není emoji. <:sadcat:576171980118687754>"

    vote_winning = "Vyhrává možnost {winning_emoji} „{winning_option}“ s {votes} hlasy."
    vote_winning_multiple = "Vyhrávají možnosti {winning_emojis} s {votes} hlasy."
    vote_none = "Čekám na hlasy."

    review_format = prefix + "review [zkratka předmětu] [tier] (anonym) (text)"
    review_wrong_subject = "Nesprávná zkratka předmětu"
    review_tier = "Tier je z rozsahu 0-3"
    review_text_len = "Maximální počet znaků v části 'text' je 1024"
    review_added = "Hodnocení předmětu bylo přidáno"
    review_get_format = prefix + "get_reviews [zkratka předmětu]"

    pr_meme = "https://github.com/Toaster192/rubbergod/pulls"
    uhoh = "uh oh"

    info = [[('karma', 'Vypíše vaši karmu, kolik pozitivní a negativní karmy'
                       ' jste rozdali.'),
             ('karma stalk [user]', 'Vypíše karmu uživatele, kolik pozitivní '
                                    'a negativní karmy rozdal.'),
             ('karma get',
              'Vypíše, které emoty mají hodnotu 1 a -1.'),
             ('karma get [emote]',
              'Vrátí karma hodnotu emotu.'),
             ('karma vote',
              'Odstartuje hlasování o hodnotě zatím neohodnoceného emotu.'),
             ('karma revote [emote]',
              'Odstartuje hlasování o nové hodnotě emotu.'),
             ('leaderboard', 'Karma leaderboard'),
             ('bajkarboard', 'Karma leaderboard reversed'),
             ('givingboard', 'Leaderboard rozdávání pozitivní karmy.'),
             ('ishaboard', 'Leaderboard rozdávání negativní karmy.')],
            [(review_format[1:], 'Přidá recenzi na předmět.'),
             (review_get_format[1:], 'Vypíše recenze na vybraný předmět.'),
             ('roll X Y',
              'Vygeneruje náhodné celé číslo z intervalu <**X**, **Y**>.'),
             ('flip', 'Hodí mincí'),
             ('pick *Is foo bar? Yes No Maybe*',
              'Vybere jedno ze slov za otazníkem.'),
             ('diceroll', 'Všechno možné házení kostkami.'),
             ('week', 'Vypíše, kolikátý je zrovna týden '
                      'a jestli je sudý nebo lichý.'),
             ('uhoh', 'Vypíše počet uh ohs od spuštění.'),
             ('uptime', 'Vypíše čas spuštění a čas uplynulý od spuštění.'),
             ('god', 'Vypíše tuto zprávu.')]]
