class Messages:

    def __init__(self):
        self.server_warning = "Tohle funguje jen na VUT FIT serveru."
        self.toaster_pls = "Toaster pls, máš bordel v DB."

        self.botroom_redirect = "{} <:sadcat:576171980118687754> 👉 " \
                                "<#{}>\n"

        self.karma_own = "{user}, tvoje karma je: **{karma}** (**{pos}.**)."
        self.karma_given = "{user}, rozdal jsi:\n" \
                           "**{karma_pos}** pozitivní karmy " \
                           "(**{karma_pos_pos}.**)\n" \
                           "**{karma_neg}** negativní karmy " \
                           "(**{karma_neg_pos}.**)"

        self.karma_vote_format = "Neočekávám argument. " \
                                 "Správný formát: `!karma vote`"
        self.karma_vote_message_hack = "Hlasování o karma ohodnocení emotu"
        self.karma_vote_message = self.karma_vote_message_hack + " {emote}"
        self.karma_vote_info = "Hlasování skončí za **{delay}** " \
                               "minut a minimální počet hlasů je " \
                               "**{minimum}**."
        self.karma_vote_result = "Výsledek hlasování o emotu {emote} " \
                                 "je {result}."
        self.karma_vote_notpassed = "Hlasovani o emotu {emote} neprošlo\n" \
                                    "Aspoň {minimum} hlasů potřeba."
        self.karma_vote_allvoted = "Už se hlasovalo o všech emotech."
        self.karma_revote_format = "Očekávám pouze formát: " \
                                   "`!karma revote [emote]`"
        self.karma_emote_not_found = "Emote jsem na serveru nenašel."
        self.karma_get_format = "Použití:\n" \
                                "`!karma get`: " \
                                "vypíše všechny emoty s hodnotou.\n" \
                                "`!karma get [emote]`: " \
                                "vrátí hodnotu daného emotu."
        self.karma_get = "Hodnota {emote} je {value}."
        self.karma_get_emote_not_voted = "{emote} není ohodnocen."
        self.karma_give_format = "Toaster pls, formát je " \
                                 "`!karma give [number] [user(s)]`"
        self.karma_give_format_number = "Toaster pls, formát je " \
                                        "`!karma give " \
                                        "[number, jakože číslo, " \
                                        "ne {input}] [user(s)]` "
        self.karma_give_success = "Karma byla úspěšně přidaná."
        self.karma_give_negative_success = "Karma byla úspěšně odebraná."

        self.role_add_denied = "{user}, na přidání role {role} nemáš právo."
        self.role_remove_denied = "{user}, " \
                                  "na odebrání role {role} nemáš právo."
        self.role_invalid_line = "{user}, řádek `{line}` je neplatný."
        self.role_format = "{user}, použij `!god`."
        self.role_not_on_server = "Nepíšeš na serveru, " \
                                  "takže předpokládám, " \
                                  "že myslíš role VUT FIT serveru."
        self.role_not_role = "{user}, {not_role} není role."
        self.role_invalid_emote = "{user}, {not_emote} " \
                                  "pro roli {role} není emote."

        self.rng_generator_format = "Použití: `!roll x [y]`\n" \
                                    "x, y je rozmezí čísel,\n" \
                                    "x, y jsou celá čísla,\n" \
                                    "pokud y není specifikováno, " \
                                    "je považováno za 0."
        self.rng_generator_format_number = "{user}, zadej dvě celá čísla, " \
                                           "**integers**."

        self.rd_too_many_dice_in_group = "Příliš moc kostek v jedné " \
                                         "skupině, maximum je {maximum}."
        self.rd_too_many_dice_sides = "Příliš moc stěn na kostkách, " \
                                      "maximum je {maximum}."
        self.rd_too_many_dice_groups = "Příliš moc skupin kostek, " \
                                       "maximum je {maximum}."
        self.rd_format = "Chybná syntax hodu ve skupině {group}."
        self.rd_help = "Formát naleznete na " \
                       "https://wiki.roll20.net/Dice_Reference\n" \
                       "Implementovány featury podle obsahu: **8. Drop/Keep**"

        self.verify_already_verified = "{user} Už jsi byl verifikován " \
                                       "({toaster} pls)."
        self.verify_send_format = "Očekávám jeden argument. " \
                                  "Správný formát: " \
                                  "`!getcode [FIT login, " \
                                  "ve tvaru xlogin00]`"
        self.verify_send_dumbshit = "{user} Tvůj login. {emote}"
        self.verify_send_success = "{user} Kód byl odeslán na tvůj mail " \
                                   "(@stud.fit.vutbr.cz)!\n" \
                                   "Pro verifikaci použij: " \
                                   "`!verify [login] [kód]`"
        self.verify_send_not_found = "{user} Login nenalezen " \
                                     "nebo jsi už tímhle krokem " \
                                     "prošel ({toaster} pls)."
        self.verify_verify_format = "Očekávám dva argumenty. " \
                                    "Správný formát: " \
                                    "`!verify [FIT login] [kód]`\n" \
                                    "Pro získání kódu použij " \
                                    "!getcode [FIT login, ve tvaru xlogin00]`"
        self.verify_verify_dumbshit = "{user} Kód, " \
                                      "který ti přišel na mail. {emote}"
        self.verify_verify_manual = "Čauec {user}, nechám {toaster}, " \
                                    "aby to udělal manuálně, " \
                                    "jsi shady (Year: {year})"
        self.verify_verify_success = "{user} Gratuluji, byl jsi verifikován!"
        self.verify_verify_not_found = "{user} Login nenalezen nebo " \
                                       "jsi už tímhle krokem prošel " \
                                       "({toaster} pls)."
