class Messages:
    server_warning = "Tohle funguje jen na VUT FIT serveru."
    toaster_pls = "Toaster pls, máš bordel v DB."

    karma_own = "{user}, tvoje karma je: **{karma}** (**{pos}.**)."
    karma_given = "{user}, rozdal jsi:\n" \
                  "**{karma_pos}** pozitivní karmy " \
                  "(**{karma_pos_pos}.**)\n" \
                  "**{karma_neg}** negativní karmy " \
                  "(**{karma_neg_pos}.**)"

    karma_vote_format = "Neočekávám argument. " \
                        "Správný formát: `!karma vote`"
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
                          "`!karma revote [emote]`"
    karma_emote_not_found = "Emote jsem na serveru nenašel."
    karma_get_format = "Použití:\n" \
                       "`!karma get`: " \
                       "vypíše všechny emoty s hodnotou.\n" \
                       "`!karma get [emote]`: " \
                       "vrátí hodnotu daného emotu."
    karma_get = "Hodnota {emote} je {value}."
    karma_get_emote_not_voted = "{emote} není ohodnocen."
    karma_give_format = "Toaster pls, formát je " \
                        "`!karma give [number] [user(s)]`"
    karma_give_format_number = "Toaster pls, formát je " \
                               "`!karma give " \
                               "[number, jakože číslo, " \
                               "ne {input}] [user(s)]` "
    karma_give_success = "Karma byla úspěšně přidaná."
    karma_give_negative_success = "Karma byla úspěšně odebraná."

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

    rng_generator_format = "Použití: `!roll x [y]`\n" \
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
                         "`!getcode [FIT login, " \
                         "ve tvaru xlogin00]`"
    verify_send_dumbshit = "{user} Tvůj login. {emote}"
    verify_send_success = "{user} Kód byl odeslán na tvůj mail " \
                          "(@stud.fit.vutbr.cz)!\n" \
                          "Pro verifikaci použij: " \
                          "`!verify [login] [kód]`"
    verify_send_not_found = "{user} Login nenalezen " \
                            "nebo jsi už tímhle krokem " \
                            "prošel ({toaster} pls)."
    verify_verify_format = "Očekávám dva argumenty. " \
                           "Správný formát: " \
                           "`!verify [FIT login] [kód]`\n" \
                           "Pro získání kódu použij " \
                           "!getcode [FIT login, ve tvaru xlogin00]`"
    verify_verify_dumbshit = "{user} Kód, " \
                             "který ti přišel na mail. {emote}"
    verify_verify_manual = "Čauec {user}, nechám {toaster}, " \
                           "aby to udělal manuálně, " \
                           "jsi shady (Year: {year})"
    verify_verify_success = "{user} Gratuluji, byl jsi verifikován!"
    verify_verify_not_found = "{user} Login nenalezen nebo " \
                              "jsi už tímhle krokem prošel " \
                              "({toaster} pls)."

    info = [('roll X Y',
             'Generates random integer from interval <**X**, **Y**>'),
            ('flip', 'Flips a coin'),
            ('pick *Is foo bar ? Yes No Maybe*',
             'Picks one of words after questionmark'),
            ('karma', 'Returns your karma stats'),
            ('karma given',
             'Returns your karma stats about how much you\'ve given'),
            ('karma get',
             'Returns a list of all non-zero valued emotes'),
            ('karma get *emote*',
             'Returns the karma value of an emote'),
            ('karma vote',
             'Odstartuje hlasovani o hodnote zatim neohodnoceneho emotu'),
            ('karma revote *emote*',
             'Odstartuje hlasovani o nove hodnote emotu'),
            ('leaderboard', ' Karma leaderboard'),
            ('bajkarboard', 'Karma leaderboard reversed'),
            ('givingboard', 'Karma leaderboard of giving positive karma'),
            ('ishaboard', 'Karma leaderboard of giving negative karma'),
            ('diceroll', 'all kinds of dice rolling'),
            ('week', 'Returns the current week (and if it\'s odd/even)'),
            ('god', 'Prints this message')]
