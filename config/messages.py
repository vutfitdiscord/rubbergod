from config.app_config import config


class Messages:
    prefix = config.default_prefix

    server_warning = "Tohle funguje jen na VUT FIT serveru."

    help_title = "Nápověda"
    help_description = "Kompletní seznam lze také najít ve veřejné administraci bota (https://public.grillbot.cloud/)"
    help_command_not_found = "Žádný příkaz jako `{command}` neexistuje."

    karma_get_missing = "Toaster pls, měl jsi bordel v DB. Musel jsem za tebe uklidit."
    missing_perms = "Na tohle nemáš práva, {user}"
    acl_help = "{user}, Použití:\n`!acl {{action}} {{table}} [args]`\n"\
               "action: add, edit, del nebo list\n"\
               "table: group, rule, role nebo user\n"\
               "Argumenty záleží na zvolené akci a tabulce: "\
               "pro přidání groupy musíte zadat název groupy a ID rodiče jako nepovinný argument."
    acl_add_group = "Group vytvořena."
    acl_edit_group = "Group změněna."
    acl_del_group = "Group smazána."
    acl_add_rule = "Pravidlo vytvořeno."
    acl_edit_rule = "Pravidlo změněno."
    acl_del_rule = "Pravidlo smazáno."
    acl_add_role = "Výjimka pro roli přidána."
    acl_edit_role = "Výjimka pro roli upravena."
    acl_del_role = "Výjimka pro roli smazána."
    acl_add_user = "Výjimka pro uživatele přidána."
    acl_edit_user = "Výjimka pro uživatele upravena."
    acl_del_user = "Výjimka pro uživatele smazána."
    no_such_command = "Takový příkaz neznám. <:sadcat:576171980118687754>"
    spamming = "{user} Nespamuj tolik <:sadcat:576171980118687754>"
    insufficient_rights = "{user}, na použití tohoto příkazu nemáš právo."
    helper_plus_only = "Na tohle mají práva jen Helper+. <:KKomrade:484470873001164817>"
    vote_room_only = "Tohle funguje jen v {room}."
    bot_room_redirect = "{user} <:sadcat:576171980118687754> 👉 " \
                        "<#{bot_room}>\n"
    covid_storno = "{user} <:WeirdChamp:680711174802899007>"
    uhoh_counter = "{uhohs} uh ohs od spuštění."
    uhoh_brief = "Vypíše počet uh ohs od spuštění"

    uptime_brief = "Vypíše čas spuštění a čas uplynulý od spuštění"
    uptime_message = "Up since:  `{boottime}`\nUptime:\t`{uptime}`"

    kachna_grillbot = "O Kachnu se teď stará Grillbot " \
                      "<:feelsWowMan:493152294712377354> Použij $kachna."

    karma = "{user} Karma uživatele `{target}` je: **{karma}** " \
            "(**{order}.**)\nA rozdal:\n" \
            "**{karma_pos}** pozitivní karmy " \
            "(**{karma_pos_order}.**)\n" \
            "**{karma_neg}** negativní karmy " \
            "(**{karma_neg_order}.**)"
    karma_brief = 'Vypíše stav vaší karmy (vč. rozdané a odebrané)'
    karma_stalk_brief = 'Vypíše karmu uživatele'
    karma_message_brief = 'Zobrazí karmu za zprávu'
    karma_get_brief = 'Vrátí karma hodnotu emotu'
    karma_getall_brief = 'Vypíše, které emoty mají hodnotu 1 a -1'
    karma_give_brief = 'Přidá karmu uživateli'
    karma_transfer_brief = 'Převede karmu z jednoho uživatele na druhého'
    karma_vote_brief = 'Odstartuje hlasování o hodnotě zatím neohodnoceného emotu'
    karma_revote_brief = 'Odstartuje hlasování o nové hodnotě emotu'
    karma_leaderboard_brief = 'Karma leaderboard'
    karma_bajkarboard_brief = 'Karma leaderboard reversed'
    karma_givingboard_brief = 'Leaderboard rozdávání pozitivní karmy'
    karma_ishaboard_brief = 'Leaderboard rozdávání negativní karmy'

    karma_invalid_command = "Neznámý karma příkaz."
    karma_vote_format = "Neočekávám žádný argument. " \
                        f"Správný formát: `{prefix}karma vote`"
    karma_vote_message_hack = "Hlasování o karma ohodnocení emotu"
    karma_vote_message = f"{karma_vote_message_hack} {{emote}}"
    karma_vote_info = "Hlasování skončí za **{delay}** " \
                      "minut a minimální počet hlasů je " \
                      "**{minimum}**."
    karma_vote_result = "Výsledek hlasování o emotu {emote} " \
                        "je {result}."
    karma_vote_notpassed = "Hlasování o emotu {emote} neprošlo.\n" \
                           "Bylo třeba aspoň {minimum} hlasů."
    karma_vote_allvoted = "Už se hlasovalo o všech emotech."
    karma_revote_format = "Očekávám pouze formát " \
                          f"`{prefix}karma revote [emote]`"
    karma_emote_not_found = "Emote jsem na serveru nenašel."
    karma_get_format = "Použití:\n" \
                       f"`{prefix}karma getall`: " \
                       "vypíše všechny emoty s hodnotou.\n" \
                       f"`{prefix}karma get [emote]`: " \
                       "zobrazí hodnotu daného emotu."
    karma_get = "Hodnota {emote} je {value}."
    karma_get_emote_not_voted = "{emote} není ohodnocen."
    karma_give_format = "Toaster pls, formát je " \
                        f"`{prefix}karma give [number] [user(s)]`"
    karma_give_format_number = "Toaster pls, formát je " \
                               f"`{prefix}karma give " \
                               "[number, jakože číslo, " \
                               "ne {input}] [user(s)]` "
    karma_give_success = "Karma byla úspěšně přidána."
    karma_give_negative_success = "Karma byla úspěšně odebrána."
    karma_message_format = f"{prefix}karma message [url]"
    member_not_found = "{user} Nikoho takového jsem nenašel."
    karma_lederboard_offser_error = "{user} Špatný offset, zadej kladné číslo"
    karma_web_title = "Celý leaderboard"
    karma_web = "https://karma.grillbot.cloud/"
    karma_transfer_format = f"Správný formát je `{prefix} karma transfer [od koho] [komu]`"
    karma_transfer_complete = "Karma byla úspěšně převedena z `{from_user}` na `{to_user}`:\n" \
                              "Množství karmy: **{karma}**\n" \
                              "Množství pozitivně rozdané karmy: **{positive}** \n" \
                              "Množství negativně rozdané karmy: **{negative}**"

    role_add_denied = "{user}, na přidání role {role} nemáš právo."
    role_remove_denied = "{user}, na odebrání role {role} nemáš právo."
    role_invalid_line = "{user}, řádek `{line}` je neplatný."
    role_format = "{user}, použij `!god`."
    role_not_on_server = "Nepíšeš na serveru, takže předpokládám, že myslíš role VUT FIT serveru."
    role_not_role = "{user}, {not_role} není role."
    role_invalid_emote = "{user}, {not_emote} pro roli {role} není emote."
    role_channel_copy_brief = 'Zkopíruje opravnění z jednoho kanálu na druhý'
    role_channel_clone_brief = 'Naklonuje kanál'

    random_diceroll_brief = 'Všechno možné házení kostkami'
    random_roll_brief = 'Vygeneruje náhodné celé číslo z intervalu <**first**, **second**>'
    random_flip_brief = 'Hodí mincí'
    random_pick_brief = 'Vybere jedno ze slov za otazníkem'
    random_pick_usage = '*Is foo bar? Yes No Maybe*'

    rng_generator_format = f"Použití: `{prefix}roll x [y]`\n" \
                           "rozmezí x, y jsou celá čísla,\n" \
                           "pokud y není specifikováno, " \
                           "je považováno za 0."
    rng_generator_format_number = "{user}, zadej dvě celá čísla, **integers**."

    rd_too_many_dice_in_group = "Příliš kostek v jedné " \
                                "skupině, maximum je {maximum}."
    rd_too_many_dice_sides = "Příliš stěn na kostkách, " \
                             "maximum je {maximum}."
    rd_too_many_dice_groups = "Příliš skupin kostek, " \
                              "maximum je {maximum}."
    rd_format = "Chybná syntaxe hodu ve skupině {group}."
    rd_help = "Formát naleznete na " \
              "https://wiki.roll20.net/Dice_Reference\n" \
              "Implementovány featury podle obsahu: **8. Drop/Keep**"

    get_code_brief = "Příkaz na získaní kódu pro verifikaci"
    verify_brief = "Verifikace studenta"
    verify_already_verified = "{user} Už jsi byl verifikován " \
                              "({admin} pls)."
    verify_send_format = "Očekávám jeden argument. " \
                         "Správný formát: " \
                         f"`{prefix}getcode FIT login, " \
                         "ve tvaru xlogin00, nebo MUNI UCO`"
    verify_send_dumbshit = "{user} Tvůj login. {emote}"
    verify_send_success = "{user} Kód byl odeslán na tvůj mail " \
                          "({mail})!\n" \
                          "Pro verifikaci použij: " \
                          f"`{prefix}verify [login] [kód]`"
    verify_verify_format = "Očekávám dva argumenty. " \
                           "Správný formát:\n" \
                           f"`{prefix}verify [FIT login nebo " \
                           "MUNI UCO] [kód]`\n" \
                           "Pro získání kódu použij\n" \
                           f"`{prefix}getcode [FIT login, ve tvaru " \
                           "xlogin00, nebo MUNI UCO]`"
    verify_verify_dumbshit = "{user} Kód, " \
                             "který ti přišel na mail. {emote}"
    verify_verify_manual = "Čauec {user}, nechám {admin}, " \
                           "aby to udělal manuálně, " \
                           "jsi shady (Year: {year})"
    verify_verify_success = "{user} Gratuluji, byl jsi verifikován!"
    verify_post_verify_info = "Podívej se do kanálů:\n" \
                              "<#591384273051975683> Pro přidání rolí\n" \
                              "<#489461089432633346> Pro pravidla a další info"
    server_link = "https://discord.com/channels/461541385204400138/"
    verify_verify_success_mail = "Gratuluji, byl jsi verifikován!"
    verify_post_verify_info_mail = "Podivej se do kanalu:\n" \
                              f"#add-roles - Pro přidání rolí ({server_link}591384273051975683) \n" \
                              f"#server-info - Pro pravidla a další info ({server_link}489461089432633346)"

    verify_verify_not_found = "{user} Login nenalezen nebo jsi neprošel krokem !getcode. Přečti si prosím <#591386755547136020>. ({admin} pls)."
    verify_verify_wrong_code = "{user} Špatný kód."
    verify_unknown_login = "{user} Tvůj login nebyl nalezen v databázi. ({admin} pls)"
    verify_step_done = "{user} Tímto krokem jsi už prošel. ({admin} pls)"
    invalid_login = "{user} Neplatný login. Přečti si prosím <#591386755547136020>. ({admin} pls)"

    vote_brief = "Zahájí hlasování, ve kterém je možné zvolit více možností"
    vote_one_of_brief = "Zahájí hlasování, ve kterém je možné zvolit pouze jednu možnost"
    vote_format = f"`{prefix}[single]vote [datum a čas konce]\n[otázka]\n[emoji] " \
                  "[možnost 1]\n[emoji] [možnost 2]\na tak dále`\n" \
                  "Jako datum/čas to sežere skoro všechno, před otázkou newline pls.\n" \
                  "Datum a čas jsou nepovinné argumenty. " \
                  "Pokud jsou vyplněny, bot pošle po uplynutí zprávu o výsledku. " \
                  "Příkaz singlevote vytvoří hlasování, kde lze zvolit jen jednu možnost."

    vote_not_emoji = "Na začátku možnosti '{opt}' není emoji. <:sadcat:576171980118687754>"
    vote_bad_date = "Hlasování může skončit jen v budoucnosti. <:objection:490989324125470720>"
    vote_bad_format = "Špatný formát hlasování. <:sadcat:576171980118687754>"

    vote_winning = "Prozatím vyhrává možnost {winning_emoji} „{winning_option}“ s {votes} hlasy."
    vote_winning_multiple = "Prozatím vyhrávají možnosti {winning_emojis} s {votes} hlasy."

    vote_none = "Čekám na hlasy."

    vote_result = "V hlasování „{question}“ vyhrála možnost {winning_emoji} " \
                  "„{winning_option}“ s {votes} hlasy."
    vote_result_multiple = "V hlasování „{question}“ vyhrály možnosti {winning_emojis} s {votes} hlasy."
    vote_result_none = "V hlasování „{question}“ nikdo nehlasoval. <:sadcat:576171980118687754>"

    review_add_brief = 'Přidá recenzi na předmět'
    review_get_brief = 'Vypíše recenze na vybraný předmět'
    review_remove_brief = 'Odstraní hodnocení'
    subject_add_biref = 'Manuálně přidá předmět/y do reviews databáze'
    subject_remove_biref = 'Manuálně odebere předmět/y z reviews databáze'
    subject_update_biref = 'Automaticky vyhledá a přidá předměty do reviews i subject databáze'

    review_format = f"{prefix}reviews [add, remove, zkratka předmětu]"
    review_add_format = f"{prefix}reviews add {{ZkratkaPredmetu}} {{Tier (0-4, 0 je TOP)}} (VolitelnyText)\n" \
                        "Pro anonymní příspěvek použijte DM.\nNapříklad:\n`" \
                        f"{prefix}reviews add IZP 2 text recenze`"
    review_wrong_subject = "Nesprávná zkratka předmětu."
    review_tier = "Tier je z rozsahu 0-4, kde 0 je nejlepší."
    review_added = "Hodnocení předmětu bylo přidáno."
    reviews_page_e = "Zavolej reviews znovu pro aktualizaci."
    reviews_reaction_help = "Pokud byla recenze užitečná dejte 👍, jinak 👎.\n" \
                            "Pro odstranění hlasu je možné použit 🛑.\n" \
                            "Použijte reakce ◀️ a ▶️ pro navigaci mezi recenzemi.\n" \
                            "Pro navigaci v textu delších recenzí použijte 🔼 a 🔽.\n"

    review_get_format = f"{prefix}reviews [zkratka předmětu]"
    review_remove_format = f"{prefix}reviews remove [zkratka předmětu]"
    review_remove_format_admin = f"{prefix}reviews remove [zkratka předmětu, id + číslo]"
    review_remove_id_format = "reviews remove id [id]"
    review_remove_success = "Hodnocení předmětu bylo odebráno."
    review_remove_error = "Hodnocení předmětu nebylo nalezeno."
    review_add_denied = "{user}, na přidání hodnocení předmětu nemáš právo."
    review_not_on_server = "{user}, na použití tohto příkazu musíš být na FITwide serveru."
    review_legacy_clicked = "Toto review je zastaralé a již není podporováno"
    subject_format = f"{prefix}subject [add, remove, update] [zkratka předmětu]"
    subject_update_error = "Aktualizace se nezdařila."
    subject_update_success = "Předměty byly úspěšně aktualizovány."
    shorcut_brief = "Vrací stručné informace o předmětu"
    shorcut_format = f"{prefix}{{command}} [zkratka předmětu]"
    tierboard_brief = "Založeno na `reviews` z průměru tier hodnot"
    tierboard_help = "Založeno na `reviews` z průměru tier hodnot.\n"\
                     "typ -> P, V, PVT, PVA\n"\
                     "semestr -> Z, L\n"\
                     "rok -> jen pro povinné předměty e.g 1BIT, 2NADE"
    tierboard_missing_year = f"Nezadal jsi rok a nemáš školní roli\n{tierboard_help}"

    pr_meme = "https://github.com/Toaster192/rubbergod/pulls"
    uhoh = "uh oh"
    question = ["<:what:638277508541710337>",
                "<:wuuut:484470874003472394>",
                "nech mě <:sadcat:576171980118687754>"]

    name_day_cz = "Dnes má svátek {name}"
    name_day_cz_brief = "Vypíše, kdo má dnes svátek"
    name_day_sk = "Dnes má meniny {name}"
    name_day_sk_brief = "Vypíše, kto má dnes meniny"

    repost_title = "Nápověda"
    repost_description = "{user}, shoda **{value}**!"
    repost_content = "Pokud je obrázek repost, dej mu ♻️.\nJestli není, klikni tady na ❎ "\
                     "a při {limit} takových reakcích se toho upozornění smaže."

    absolvent_wrong_diploma_format = "Chybný formát čísla diplomu! Př: 123456/2019"
    absolvent_wrong_name = "Nepovedla se ověřit shoda zadaného jména s tvým předchozím záznamem o studiu na FIT VUT."
    absolvent_thesis_not_found_error = "Práce dle zadaného ID nebyla na webu nalezena."
    absolvent_web_error = "Nepovedlo se ověřit obhájení kvalifikační práce pod uvedeným číslem na webu, jménem, typem práce a rokem obhájení (dle čísla diplomu)."
    absolvent_diploma_error = "Diplom (číslo a jméno) se nepovedlo na webu ověřit."
    absolvent_success = "Diplom byl úspěšne ověřen."
    absolvent_id_from_help = "Zadej svoje ID práce."
    absolvent_brief = "Příkaz pro ověření absolvování studia na FIT VUT"
    absolvent_help = f"{absolvent_brief} - zadejte CASE-SENSITIVE údaje ve formátu:\n" \
        f"{prefix}{{command}} <Titul.> <Jméno> <Příjmení> <Číslo diplomu> <ID kvalifikační práce z URL na webu knihovny VUT <https://dspace.vutbr.cz/handle/11012/19121> >\n" \
        "např: Bc. Josef Novák 123456/2019 99999\n" \
        "(při <https://dspace.vutbr.cz/handle/11012/99999>)\n" \
        "Údaje slouží k jednorázovému ověření a nejsou nikam ukládány."

    urban_brief = "Vyhledávaní výrazu v urban slovníku"
    urban_help = f"`{prefix}urban výraz`\nPříklad:\n`{prefix}urban sure`"
    urban_not_found = "Pro daný výraz neexistuje záznam <:sadcat:576171980118687754>"

    autopin_max_pins_error = "Byl dosažen maximální počet připnutých zpráv."
    autopin_add_brief = "Začne sledovat zprávu jako prioritní pin.\n"
    autopin_add_unknown_message = "Očekáváno URL zprávy"
    autopin_add_done = "Priorita pinu nastavena."
    autopin_remove_brief = "Odebere sledování prioritního pinu."
    autopin_remove_not_exists = "V kanálu {channel_name} není nastavena prioritní zpráva pro piny."
    autopin_remove_done = "Priorita pinu odebrána."
    autopin_no_messages = "Ještě neexistuje žádné mapování."
    autopin_list_brief = "Zobrazí všechny piny s nastevenou prioritou"
    autopin_list_unknown_channel = "> Neznámý kanál ({channel_id})"
    autopin_list_unknown_message = "> {channel} - Neznámá zpráva"
    autopin_list_item = "> {channel} - {url}"

    on_ready_message = "<:peepowave:693070888546861096>"

    git_pull_brief = 'Stáhne aktuálni změny z repa'

    cogs_brief = 'Vypíše seznam načtených cogs'
    cog_load_brief = 'Načte cog'
    cog_unload_brief = 'Odebere cog'
    cog_reload_brief = 'Znovu načte cog'
    cog_is_loaded = 'Toto rozšíření `{cog}` je již načtené.'
    cog_unloaded = 'Rozšíření `{cog}` odebráno.'
    cog_loaded = 'Rozšíření `{cog}` načteno.'
    cog_is_unloaded = 'Toto rozšíření `{cog}` není načteno'
    cog_cannot_be_unloadable = 'Toto rozšíření `{cog}` je neodebratelné.'
    cog_reloaded = 'Rozšíření `{cog}` bylo načteno znovu.'

    config_backup_brief = "Vytvoří záložní kopii konfigurace v novém souboru"
    config_get_brief = "Získa hodnotu z konfigurace"
    config_set_brief = "Nastaví hodnotu v konfiguraci"
    config_append_brief = "Přidá hodnotu do pole v konfiguraci"
    config_load_brief = "Znovu načíta třídu ze souboru. Pro aplikováni změn je potřeba znovu načíst i cog"
    config_list_brief = "Vypíše klíče konfigurace"
    config_updated = 'Config updated'
    config_loaded = 'Config loaded'
    config_wrong_key = 'Nesprávny klíč'
    config_wrong_type = 'Nesprávny typ'
    config_backup_created = 'Config backup created'
    config_append_format = f'{prefix}config append [key] hodnota/y'
    config_list_invalid_regex = 'Chybný regex\n`{regex_err}`'
    config_sync_template_brief = 'Synchronizuje config s template, přidá chybějíci klíče'
    config_synced = 'Config byl synchronizován'

    channel_help = f"{prefix}channel [clone, copy]"
    channel_copy_help = f"{prefix}channel copy [source] [destination]"
    channel_copy_done = "Práva byla zkopírována."
    channel_clone_help = f"{prefix}channel clone [source] [jméno]"
    channel_clone_done = "Kanál <#{id}> byl vytvořen."

    warden_scan_brief = "Prohledá obrázky v aktuálním kanále a uloží je jako hash pro detekci repostu.\nlimit: [all | <int>]"

    weather_brief = "Vypíše informace o počasí ve zvoleném městě"

    week_brief = "Vypíše, kolikátý je zrovna týden a jestli je sudý nebo lichý"
    week_warning = "Pro sudý/lichý se využívá kalendářní týden"

    streamlinks_brief = "Úložiště všech streamů"
    streamlinks_add_brief = "Zapíše nový stream k předmětu"
    streamlinks_add_link_exists = "Tento stream již existuje."
    streamlinks_add_success = "Stream byl úspěšně vytvořen <:HYPERS:493154327318233088>"
    streamlinks_add_format = f"`{prefix}streamlinks add [zkratka předmětu] [link] [Kdo (Jméno, nebo Tag)] [Datum nahrání(Volitelně)] [Popis]`\n\n"\
        "Datum nahrání se bere následovně. Nejdříve se pokusí získat automaticky ze služby, odkud odkaz pochází (youtube, ...), "\
        "pokud ze služby, kde je video nahráno nepůjde získat datum, tak bot zjistí, zda nebyl zadán jako volitelný parametr před popisem. "\
        "Datum se zadává ve formátu `{Rok}-{Měsíc}-{Den}`. Pokud ani tam nebude zadán datum, tak se jako datum nahrání bere aktuální datum.\n\n"\
        f"Příklad volání:\n`{prefix}streamlinks add izp https://youtu.be/randomlink Rubbergod Ten nejlepší stream ever kappa.`"
    streamlinks_unsupported_embed = "Tento seznam již není podporován. Zavolej znovu příkaz pro aktualizaci."
    streamlinks_not_actual = "Tento seznam již není aktuální. Zavolej znovu příkaz pro aktualizaci."
    streamlinks_missing_original = "Originální zpráva s příkazem byla smazána. Zavolej znovu příkaz a nemaž originální zprávu."
    streamlinks_list_brief = "Vypíše zjednodušený seznam všech streamů k daném předmětu."
    streamlinks_list_format = f"`{prefix}streamlinks list [zkratka předmětu]`"
    streamlinks_no_stream = "K tomuto předmětu ještě neexistuje žádný stream."
    streamlinks_missing_description = "Nebyl zadán popis linku."
    streamlinks_remove_brief = "Smazání streamu z předmětu."
    streamlinks_remove_format = f"`{prefix}streamlinks remove [id]`\n\nID se nachází v patičce embedu. Na konci v textu v závorce, kde je # (Jen to číslo je ID)."
    streamlinks_not_exists = "Stream s tímto ID nebyl nalezen."
    streamlinks_remove_prompt = "Opravdu chceš tento stream odstranit ({link})?"
    streamlinks_remove_success = "Stream <{link}> byl úspěšně smazán."

    latex_help = f"Příklad:\n`{prefix}latex x^n + y^n = z^n`"
    latex_desc = "Vykreslí LaTeX výraz"

    bonk_brief = "Bonk na uživatele"
    unsupported_image = "Tento avatar aktuálne není podporovaný <:sadcat:576171980118687754>"

    subscribe_brief = "Přihlášení k odběru zpráv kanálu do DM"
    unsubscribe_brief = "Odhlášení odběru zpráv do DM"
    subscribeable_brief = "Výpis kanálů které je možné sledovat"
    subscriptions_brief = "Výpis odběrů zpráv uživatele nebo kanálu"
    subscriptions_embed_name = "Informace o zprávě"
    subscriptions_embed_value = "Zpráva obsahuje přílohy."
    subscriptions_message_link = "Odkaz na zprávu"
    subscriptions_unsubscribable = "Tento kanál odebírat nemůžeš."
    subscriptions_already_subscribed = "Tuto místnost již odebíráš."
    subscriptions_new_subscription = "Upozornění na nové zprávy ti budu posílat do DM."
    subscriptions_not_subscribed = "Tuto místnost neodebíráš."
    subscriptions_unsubscribed = "Nová upozornění na zprávy ti už posílat nebudu."
    subscriptions_none = "Nebyly nalezeny žádné výsledky."
    subscriptions_missing_argument = "Musíš specifikovat kanál."
    subscriptions_bad_argument = "Musíš specifikovat kanál nebo uživatele."

    studijni_brief = "Úřední hodiny studijního Oddělení"
    studijni_web_error = "Chyba při parsování webu"
    studijni_office_hours = "Úřední hodiny"
    studijni_title = "C109 Studijní oddělení"

    fit_room_brief = "Zobrazení místnosti na plánku fakulty."
    fit_room_help = f"{prefix}room <místnost>"
    fit_room_unreach = "Stránka s plánkem je nedostupná."
    fit_room_parsing_failed = "Načtení stránky s plánkem se nezdařilo. Nahlaš prosím tuto chybu správci bota."
    fit_room_room_not_on_plan = "Zadaná místnost {room} není na plánku nebo neexistuje."

    meme_repost_link = "[Odkaz na originál]({original_message_url}) v <#{original_channel}>"

    exams_brief = f"{prefix}exams [rocnik] pro zobrazení zkoušek pro daný ročník a nebo bez ročníku pro ročník podle role"
    exams_no_valid_role = "Nebyla nalezena ročníková role"
    exams_specify_year = "Specifikuj ročník"
    exams_no_valid_year = "Byl zadán neplatný ročník"
    exams_parsing_failed = "Parsing stránky selhal, nahlaš chybu správci bota"
    exams_update_term_brief = "Aktualizuje termíny v kanálech termínů"
    exams_remove_all_terms_brief = "Odstraní termíny ze všech kanálů termínů"
    exams_remove_terms_brief = "Odstraní termíny ze zadaného kanálu"
    exams_start_terms_brief = "Zapne automatickou aktualizaci termínů"
    exams_stop_terms_brief = "Vypne automatickou aktualizaci termínů"
    exams_terms_updated = "`Termíny aktualizovány`"
    exams_terms_removed = "`Termíny odstraněny`"
    exams_nothing_to_remove = "`Nenalezeny žádné termíny v kanálu {name}`"
    exams_channel_is_not_text_channel = "`Nenalezeny žádné termíny v kanálu {name}`"
    exams_automatic_update_started = "`Zapnuta automatická aktualizace termínů pro server: {name}`"
    exams_automatic_update_stopped = "`Zastavena automatická aktualizace termínů pro server: {name}`"
