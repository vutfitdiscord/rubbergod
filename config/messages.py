from config.app_config import config
from features.callable_string import Formatable


class Messages(metaclass=Formatable):
    # GENERAL MESSAGES
    prefix = config.default_prefix

    server_warning = "Tohle funguje jen na VUT FIT serveru."

    help_title = "Nápověda"
    help_description = "Kompletní seznam lze také najít ve veřejné administraci bota (https://public.grillbot.eu/)"

    karma_get_missing = "Toaster pls, měl jsi bordel v DB. Musel jsem za tebe uklidit."

    on_ready_message = "<:peepowave:693070888546861096>"
    cooldown = "Příliš rychle, zkus to znovu za {time:.3}s"
    embed_not_author = "Hraj si na svém písečku s tebou zavolanými příkazy. <:pepeGun:826943455032901643>"
    base_leaderboard_format_str = "_{position}._ - **{member_name}**:"

    # FITWIDE
    increment_roles_brief = "Aktualizuje role na serveru podle ročníku. Aktualizace školních roomek."
    increment_roles_start = "Incrementing roles..."
    increment_roles_names = "1/3 - Role úspěšně přejmenovány a 0bit a 0mit vytvořen"
    increment_roles_room_names = "2/3 - Kanály úspěšně přejmenovány a 0bit a 0mit general vytvořen"
    increment_roles_success = "3/3 - Holy fuck, všechno se povedlo, tak zase za rok <:Cauec:602052606210211850>"
    fitwide_role_check_brief = "Zkontroluje ročníkové role uživatelům"
    fitwide_role_check_start = "Kontrola uživatelů ..."
    fitwide_role_check_user_not_found = "Ve verified databázi jsem nenašel: {user} ({id})"
    fitwide_role_check_user_duplicate = "{user} ({id}) je v permit databázi víckrát?"
    fitwide_role_check_wrong_status = "Status nesedí u: {user} ({id})"
    fitwide_brief = "Příkazy na manipulaci verify studentů"
    fitwide_update_db_brief = "Aktualizuje databázy s loginy"
    fitwide_update_db_start = "Aktualizuji databázy..."
    fitwide_new_logins = "Našel jsem {new_logins} nových loginů."
    fitwide_update_db_done = "Aktualizace databáze proběhla úspěšně."
    fitwide_db_debug = "Debug: Našel jsem {cnt_new} nových prvaků."
    fitwide_pull_db_brief = "Stáhne databázy uživatelů na merlinovi"
    fitwide_get_db_error = "Při stahování databáze došlo k chybě."
    fitwide_get_db_timeout = "Timeout při stahování databáze."
    fitwide_get_db_success = "Stažení databáze proběhlo úspěšně."
    fitwide_get_login_brief = "Získá xlogin uživatele"
    fitwide_login_not_found = "Uživatel není v databázi."
    fitwide_get_user_brief = "Získá discord uživatele"
    fitwide_get_user_not_found = "Uživatel není v databázi možných loginů."
    fitwide_get_user_format = "Login: `{p.login}`\nJméno: `{p.name}`\n" "Ročník: `{p.year}`\n"
    fitwide_invalid_login = "To není validní login."
    fitwide_action_success = "Příkaz proběhl úspěšně."
    fitwide_reset_login_brief = "Odstraní uživatele z verify databáze"
    fitwide_link_login_user_brief = "Propojí login s uživatelem"
    fitwide_not_in_modroom = "Nothing to see here comrade. <:KKomrade:484470873001164817>"
    fitwide_login_already_exists = "Uživatel již existuje v databázi."

    # ERROR
    moved_command = "Tento příkaz již není v textové formě podporován. Příkaz byl nahrazen příkazem </{name}:{id}>"
    no_such_command = "Takový příkaz neznám. <:sadcat:576171980118687754>"
    command_timed_out = "Příkaz nereagoval a byl nečekaně ukončen."
    command_invoke_error = "Došlo k nečekané chybě, už na tom pracujeme <:notLikeRubbergod:1112395455142314044>"
    user_input_error = "Chyba ve vstupu, jestli vstup obsahuje `\"`, nahraď je za `'`"
    spamming = "{user} Nespamuj tolik <:sadcat:576171980118687754>, příkaz můžeš použít až za {time}."
    member_not_found = "{member} Nikoho takového jsem na serveru nenašel."
    user_not_found = "{user} Nikoho takového jsem nenašel."
    help_command_not_found = "Žádný příkaz jako `{command}` neexistuje."

    # PERMISSIONS
    missing_perms = "{user}, na použití tohoto příkazu nemáš právo."
    helper_plus_only = "Na tohle mají práva jen Helper+. <:KKomrade:484470873001164817>"
    submod_plus_only = "Na tohle mají práva jen Submod+. <:KKomrade:484470873001164817>"
    mod_plus_only = "Na tohle mají práva jen Mod+. <:KKomrade:484470873001164817>"
    bot_admin_only = "Na tohle mají práva jen Admin. <:KKomrade:484470873001164817>"
    vote_room_only = "Tohle funguje jen v {room}."
    guild_only = "Tento příkaz lze použít pouze na serveru."
    bot_room_redirect = "{user} <:sadcat:576171980118687754> 👉 " \
                        "<#{bot_room}>\n"

    # MEME
    uhoh_counter = "{uhohs} uh ohs od spuštění."
    uhoh_brief = "Vypíše počet uh ohs od spuštění"
    uhoh = "uh oh"

    pr_meme = "https://github.com/Toaster192/rubbergod/pulls"

    # HUGS
    hug_give_brief = "Obejme kamaráda"
    hug_intensity_description = "Síla obejmutí (číslo 1-{emoji_count})"
    hug_stats_brief = "Tvé statistiky obejmutí"
    hug_hugboard_brief = "Celková tabulka statistiky obejmutí"
    hug_huggersboard_brief = "Vypíše nejčastější objímače"
    hug_mosthugged_brief = "Vypíše nejvíce objímané lidi"
    upgraded_pocitani_caught_deleting = "Podvádět mazáním zpráv je zakázáno. Začínáme znovu: "

    # IOS
    ios_brief = "Připomene všem prasatům, že si mají jít po sobě uklidit"
    ios_task_start_brief = "Začne pravidelně připomínat všem prasatům, že si mají jít po sobě uklidit"
    ios_task_start_success = f"Automatické připomínání úspěšně nastaveno. Bude se od teď provádět každých {config.ios_looptime_minutes} minut."
    ios_task_start_already_set = "Automatické připomínání už je nastaveno."
    ios_task_stop_brief = "Zastaví automatické připomínání"
    ios_task_stop_success = "Automatické připomínání zastaveno."
    ios_task_stop_nothing_to_stop = "Automatické připomínání není nastaveno."
    ios_task_cancel_brief = "Okamžitě ukončí automatické připomínání (přeruší aktuální běh)"
    ios_parsing_error = "Toastere, máš bordel v parsování."
    ios_howto_clean = "Pokud nevíte, jak po sobě uklidit, checkněte: https://discordapp.com/channels/461541385204400138/534431057001316362/698701631495340033"

    # KARMA
    karma = "{user} Karma uživatele `{target}` je: **{karma}** " \
            "(**{order}.**)\nA rozdal:\n" \
            "**{karma_pos}** pozitivní karmy " \
            "(**{karma_pos_order}.**)\n" \
            "**{karma_neg}** negativní karmy " \
            "(**{karma_neg_order}.**)"
    karma_brief = "Vypíše stav vaší karmy (vč. rozdané a odebrané)"
    karma_stalk_brief = "Vypíše karmu uživatele"
    karma_message_brief = "Zobrazí karmu za zprávu"
    karma_get_brief = "Vrátí karma hodnotu emotu"
    karma_getall_brief = "Vypíše, které emoty mají hodnotu 1 a -1"
    karma_give_brief = "Přidá karmu uživateli"
    karma_transfer_brief = "Převede karmu z jednoho uživatele na druhého"
    karma_vote_brief = "Odstartuje hlasování o hodnotě zatím neohodnoceného emotu"
    karma_revote_brief = "Odstartuje hlasování o nové hodnotě emotu"
    karma_leaderboard_brief = "Karma leaderboard"
    karma_givingboard_brief = "Leaderboard rozdávání pozitivní/negativní karmy"
    karma_board_start = "Zobrazí leaderboard na dané pozici"

    karma_invalid_command = "Neznámý karma příkaz."
    karma_vote_message_hack = "Hlasování o karma ohodnocení emotu"
    karma_vote_message = f"{karma_vote_message_hack} {{emote}}\n"
    karma_vote_info = "Hlasování skončí za **{delay}** " \
                      "minut a minimální počet hlasů je " \
                      "**{minimum}**."
    karma_vote_result = "Výsledek hlasování o emotu {emote} " \
                        "je {result}."
    karma_vote_notpassed = "Hlasování o emotu {emote} neprošlo.\n" \
                           "Bylo třeba aspoň {minimum} hlasů."
    karma_vote_allvoted = "Už se hlasovalo o všech emotech."
    karma_revote_not_emoji = "Špatný formát emoji."
    karma_revote_started = "Hlasování o nové hodnotě emotu začalo."
    emote_not_found = "Emote `{emote}` jsem na serveru nenašel."
    karma_get_format = "Použití:\n" \
                       "`/karma getall`: " \
                       "vypíše všechny emoty s hodnotou.\n" \
                       "`/karma get [emote]`: " \
                       "zobrazí hodnotu daného emotu."
    karma_get = "Hodnota {emote} je {value}."
    karma_getall_response = "Ohodnocené emoji:"
    karma_get_emote_not_voted = "{emote} není ohodnocen."
    karma_give_success = "Uživateli {user_list} bylo úspěšně přidáno **{karma} karmy**."
    karma_give_negative_success = "Uživateli {user_list} bylo úspěšně odebráno **{karma} karmy**."
    karma_message_format = "Musíš zadat url zprávy"
    karma_leaderboard_offset_error = "{user} Špatný offset, zadej kladné číslo"
    karma_web_title = "Celý leaderboard"
    karma_web = "https://karma.grillbot.eu/"
    karma_transfer_same_user = "Nelze převést karmu na stejného uživatele."
    karma_transer_user_no_karma = "{user} nemá žádnou karmu."
    karma_transfer_complete = "Karma byla úspěšně převedena z `{from_user}` na `{to_user}`:\n" \
                              "Množství karmy: **{karma}**\n" \
                              "Množství pozitivně rozdané karmy: **{positive}** \n" \
                              "Množství negativně rozdané karmy: **{negative}**"

    # GIF
    bonk_brief = "Bonk na uživatele"
    unsupported_image = "Tento avatar aktuálne není podporovaný <:sadcat:576171980118687754>"
    pet_brief = "Vytvoří gif z uživatele."
    gif_req_error = "Nepodařilo se získat profilový obrázek uživatele."

    # ROLES
    role_add_denied = "{user}, na přidání role {role} nemáš právo."
    role_remove_denied = "{user}, na odebrání role {role} nemáš právo."
    role_invalid_line = "{user}, řádek `{line}` je neplatný."
    role_format = "{user}, použij `!god`."
    role_not_on_server = "Nepíšeš na serveru, takže předpokládám, že myslíš role VUT FIT serveru."
    role_not_role = "{user}, {not_role} není role."
    role_invalid_emote = "{user}, {not_emote} pro roli {role} není emote."
    role_channel_copy_brief = "Zkopíruje opravnění z jednoho kanálu na druhý"
    role_channel_clone_brief = "Naklonuje kanál"
    role_channel_create_brief = "Vytvoří privátní text kanál pro uživatele z konkrétní role."

    role_create_start = "Migrace oprávnění na roli pro **{role}**"
    role_create_progress = "Migrace pro #{channel} • uživatelů: {perms} {progress}"
    role_create_done = "Migrace oprávnění na roli **{role}** dokončena. Počet oprávnění: {perms}"
    role_migration_allert = "Přidání/Odebrání **{channel}** bude trvat déle než je obvyklé (až 30 min)." \
                            "Prosím o strpení. Opakované klikání na reakce nemá vliv na dobu zpracování přístupu."

    remove_exclusive_roles = "Odstraní konflikty rolí, kdy má uživatel více exkluzivních rolí."
    remove_exclusive_roles_start = "Probíhá odstraňování konfliktů rolí {role1} a {role2}"
    role_no_exlusives = "Nebyly nalezeny žádné konflikty rolí"
    remove_exclusive_roles_done = "Úspěšně odstraněny konflikty rolí"
    role_to_remove = "Role, která se má odstranit"

    channel_copy_start = "Probíhá kopírování kanálu"
    channel_copy_done = "Práva byla zkopírována."
    channel_clone_start = "Probíhá klonování kanálu"
    channel_clone_done = "Kanál <#{id}> byl vytvořen."
    channel_create_start = "Probíhá vytváření kanálu"
    channel_create_done = "Vytvoření kanálu bylo úspěšné, kanál {channel} vytvořen s přístupem pro roli **{role}**.\n • Počet overwrites: **{perms}**"
    channel_rate = "Po kolika částech aktualizovat progress bar."
    channel_get_overwrites_brief = "Vypíše počet přístupových práv pro všechny mistnosti"
    channel_get_overwrites_start = "Probíhá získávání přístupových práv"
    channel_get_overwrites_done = "Získávání přístupových práv bylo úspěšné"
    channel_role_to_overwrites_brief = "Vytvoří roli z přístupových práv"
    channel_role_to_overwrites_start = "Probíhá převádění role na přístupová práva"
    channel_role_to_overwrites_done = "Role úspěšně převedena na přístupová práva"
    channel_overwrites_to_role_brief = "Vytvoří overwrites na místnost z role"
    channel_overwrites_to_role_start = "Probíhá převádění přístupových práv na roli"
    channel_overwrites_to_role_done = "Přístupová práva byla úspěšně převedena na roli"

    group_add = "Přidá skupinu"
    group_get = "Vypíše informace o skupině"
    group_delete = "Smaže skupinu"
    group_list = "Vypíše všechny skupiny"
    group_add_channel_id = "Přidá místnost do skupiny"
    group_add_role_id = "Přidá roli do skupiny"
    group_reset_channels = "Resetuje kanály pro skupinu"
    group_reset_roles = "Resetuje role pro skupinu"

    # RANDOM
    random_roll_brief = "Vygeneruje náhodné celé číslo z intervalu <**first**, **second**>"
    random_flip_brief = "Hodí mincí"
    random_pick_brief = "Vybere jedno ze slov za otazníkem."
    random_pick_format = "*Is foo bar? Yes No Maybe*"
    random_pick_empty = "Nenapsal jsi žádné možnosti k otázce."

    rng_generator_format = f"Použití: `{prefix}roll x [y]`\n" \
                           "rozmezí x, y jsou celá čísla,\n" \
                           "pokud y není specifikováno, " \
                           "je považováno za 0."

    # VERIFY
    verify_brief = "Ověření studenta pro přístup na server."
    verify_login_parameter = "Přihlašovací FIT login (nebo MUNI UČO). FIT login ve formátu `xlogin00`"
    verify_already_verified = "{user} Už jsi byl verifikován " \
                              "({admin} pls)."
    verify_send_dumbshit = "{user} Tvůj login. {emote}"
    verify_send_success = "Kód byl odeslán na tvůj mail (`{mail}`). " \
                          "Pokud kód do 10 minut nedorazí, tak si jej nech znovu zaslat. " \
                          "Hledej zprávu s předmětem `{subject}` (může být i ve SPAMu)."
    verify_resend_success = "Kód byl znovuodeslán na tvůj mail (`{mail}`). " \
                          "Pokud kód do 10 minut nedorazí, tak tagni někoho z Mod týmu." \
                          "Hledej zprávu s předmětem `{subject}` (může být i ve SPAMu)."
    verify_verify_manual = "Čauec {user}, nechám {admin}, aby to udělal manuálně, " \
                           "jsi shady (Year: {year})"
    verify_verify_success = "{user} Gratuluji, byl jsi verifikován!"
    verify_post_verify_info = "Role si přidáš v Channels & Roles " \
                              "(Jak na to 👉 https://discord.com/channels/461541385204400138/489461089432633346/635184378065977354)\n" \
                              "Dále se mrkni do <#489461089432633346> pro pravidla a další info"
    server_link = "https://discord.com/channels/461541385204400138/"
    verify_verify_success_mail = "Gratuluji, byl jsi verifikován!"
    verify_post_verify_info_mail = "Podívej se do kanálu " \
                              f"#server-info pro pravidla a další info ({server_link}489461089432633346)"
    verify_mail_content = "Obdržel/a jsi kód pro ověření se k přístup na server VUT FIT.\n" \
                          "Po stisknutí na tlačítko \"Zadat kód\" vyplň ověřovací kód přesně tak jak je uveden níže.\n\n" \
                          "Ověřovací kód: {code}"

    verify_verify_not_found = "{user} Login nenalezen nebo jsi neprošel krokem `/verify`. Přečti si prosím <#591386755547136020>. ({admin} pls)."
    verify_verify_wrong_code = "Špatný kód."
    verify_unknown_login = "{user} Tvůj login nebyl nalezen v databázi. ({admin} pls)"
    verify_step_done = "{user} Tímto krokem jsi už prošel. ({admin} pls)"
    verify_invalid_channel = "Tento příkaz je možné spustit pouze v DMs nebo na VUT FIT serveru."
    invalid_login = "{user} Neplatný login. Přečti si prosím <#591386755547136020>. ({admin} pls)"
    verify_subject = "FIT Discord verifikace"
    dynamic_verify_requested = "Byla zaslána žádost o verifikaci. Vyčkej prosím než ji někdo z oprávněných osob schválí."
    dynamic_verify_declined = "Tvá žádost o verifikaci byla zamítnuta."
    dynamic_verify_create_brief = "Vytvoření pravidla pro verifikaci"
    dynamic_verify_edit_brief = "Vytvoření pravidla pro verifikaci"
    dynamic_verify_rule_id = "Pravidlo k editaci"
    dynamic_verify_edit_success = "Pravidlo bylo úspěšně upraveno."
    dynamic_verify_create_success = "Pravidlo bylo úspěšně vytvořeno."
    dynamic_verify_remove_brief = "Odstranění pravidla pro verifikaci"
    dynamic_verify_remove_success = "Pravidlo bylo úspěšně odstraněno."
    dynamic_verify_rule_missing = "Nebylo zadáno platné ID pravidla."
    dynamic_verify_rule_exists = "ID s tímto pravidlem již existuje."
    dynamic_verify_invalid_state = "Nepovolený stav. Lze zadat pouze True/False"
    dynamic_verify_role_not_exists = "Role `{role}` neexistuje."
    dynamic_verify_no_roles = "Nebyla nalezena žádná role."
    dynamic_verify_missing_rule = "Toto pravidlo (`{rule_id}`) neexistuje."

    # VOTE
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

    # CONTESTVOTE
    contest_vote_calculate_message_brief = "Spočítá počet hlasů a jejich celkovou váhu pro daný příspěvek"
    contest_vote_winners_brief = "Zobrazí prvních 5 vítězných příspěvků"
    contest_vote_no_reactions = "Tato zpráva nemá žádné reakce"
    contest_vote_no_votes = "Na tuto zprávu nebyly přidány žádné hlasy"

    # REVIEW
    review_add_brief = "Přidá recenzi na předmět. Pokud jsi již recenzi na předmět napsal, bude nahrazena novou."
    review_get_brief = "Vypíše recenze na vybraný předmět"
    review_remove_brief = "Odstraní hodnocení"
    review_list_brief = "Vypíše předměty, které si již ohodnotil"
    review_id_brief = "ID recenze, pouze pro administrátory"
    review_grade_brief = "Známku, kterou by jsi dal předmětu od A-F (za organizaci, splnění očekávání, kvalitu výuky ...)"

    review_wrong_subject = "Nesprávná zkratka předmětu."
    review_added = "Hodnocení předmětu bylo přidáno."
    reviews_reaction_help = "Pokud byla recenze užitečná dejte 👍, jinak 👎.\n" \
                            "Pro odstranění hlasu je možné použit 🛑.\n" \
                            "Použijte reakce ◀️ a ▶️ pro navigaci mezi recenzemi.\n" \
                            "Pro navigaci v textu delších recenzí použijte 🔼 a 🔽.\n"
    review_vote_own = "Nemůžeš hlasovat pro vlastní recenzi"
    review_remove_success = "Hodnocení předmětu bylo odebráno."
    review_not_found = "Hodnocení předmětu nebylo nalezeno."
    review_remove_denied = "{user}, `id` je pouze pro administrátory. Pro smazání použij jen `subject`."
    review_add_denied = "{user}, na přidání hodnocení předmětu nemáš právo."
    review_not_on_server = "{user}, na použití tohoto příkazu musíš být na FITwide serveru."

    # review embed
    review_embed_description = "{name}\n**Průměrná známka od studenta:** {grade}"
    review_embed_no_reviews = "*Zatím nic*"
    review_text_label = "Text recenze"
    review_text_page_label = "Stránka textu"
    review_author_label = "Autor"
    review_grade_label = "Kvalita předmětu"
    review_date_label = "Datum"
    review_other_reviews_label = "Další hodnocení"
    review_authored_list_label = "Ohodnotil jsi:"

    # review modal
    review_modal_title = "Přidat novou recenzi"
    review_subject_label = "Vyberte předmět"
    review_anonym_label = "Anonymní recenze"
    review_signed_label = "Zobrazit nick"
    review_tier_placeholder = "Hodnocení předmětu"
    review_tier_0_desc = "Nejlepší, jednoduchý, naučí"
    review_tier_1_desc = "Naučí, ale je třeba zapracovat"
    review_tier_2_desc = "Průměrný předmět"
    review_tier_3_desc = "Nic moc"
    review_tier_4_desc = "Nejhorší, celé zle"

    subject_update_biref = "Automaticky vyhledá a přidá předměty do reviews i subject databáze"
    subject_update_overwrite_brief = "Přepíše všechny informace o předmětech. Využít pouze v kombinaci s další aktualizací bez přepisu."
    subject_update_error = "Aktualizace se nezdařila pro <{url}>\n"
    subject_update_success = "Předměty byly aktualizovány."
    shortcut_brief = "Vrací stručné informace o předmětu"
    tierboard_brief = "Založeno na `reviews` z průměru tier hodnot"
    tierboard_missing_year = f"Nezadal jsi ročník a nemáš školní roli"

    # NAMEDAY
    name_day_cz = "Dnes má svátek {name}"
    name_day_cz_brief = "Vypíše, kdo má dnes svátek"
    name_day_sk = "Dnes má meniny {name}"
    name_day_sk_brief = "Vypíše, kto má dnes meniny"
    birthday_api_error = "Hobitovi to zas nefunguje, tak nevím kdo má dnes narozeniny <:sadge:751913081285902336>"

    # WARDEN
    warden_scan_brief = "Prohledá obrázky v aktuálním kanále a uloží je jako hash pro detekci repostu.\nlimit: [all | <int>]"
    repost_title = "Nápověda"
    repost_description = "{user}, shoda **{value}**!"
    repost_content = "Pokud je obrázek repost, dej mu ♻️.\nJestli není, klikni tady na ❎ "\
                     "a při {limit} takových reakcích se toho upozornění smaže."

    # ABSOLVENT
    absolvent_wrong_diploma_format = "Chybný formát čísla diplomu! Př: 123456/2019"
    absolvent_wrong_name = "Nepovedla se ověřit shoda zadaného jména s tvým předchozím záznamem o studiu na FIT VUT."
    absolvent_thesis_not_found_error = "Práce dle zadaného ID nebyla na webu nalezena."
    absolvent_web_error = "Nepovedlo se ověřit obhájení kvalifikační práce pod uvedeným číslem na webu, jménem, typem práce a rokem obhájení (dle čísla diplomu)."
    absolvent_diploma_error = "Diplom (číslo a jméno) se nepovedlo na webu ověřit."
    absolvent_success = "Diplom byl úspěšne ověřen."
    absolvent_id_from_help = "Zadej svoje ID práce."
    absolvent_brief = "Příkaz pro ověření absolvování studia na FIT VUT"
    absolvent_help_brief = "Vypíše help k příkazu /diplom"
    absolvent_not_in_db = "Tvůj login nebyl nalezen v databázi ověřených uživatelů. Použij příkaz `/verify` pro ověření (je zapotřebí školní email)."
    absolvent_not_verified = "Pro zavolání tohoto příkazu je potřeba se ověřit pomocí příkazu `/verify`."
    absolvent_help = f"{absolvent_brief} - zadejte CASE-SENSITIVE údaje ve formátu:\n" \
        "/diplom <Titul.> <Jméno> <Příjmení> <Číslo diplomu> <ID kvalifikační práce z URL na webu knihovny VUT <https://dspace.vutbr.cz/handle/11012/19121> >\n" \
        "např: Bc. Josef Novák 123456/2019 99999\n" \
        "(při <https://dspace.vutbr.cz/handle/11012/99999>)\n" \
        "Údaje slouží k jednorázovému ověření a nejsou nikam ukládány."
    absolvent_degree_param = "Dosažený titul - Bc./Ing."
    absolvent_name_param = "Křestní jméno např.: Josef"
    absolvent_surname_param = "Příjmení např.: Novák"
    absolvent_diploma_param = "Číslo diplomu např.: 123456/2019"
    absolvent_thesis_id_param = "ID kvalifikační práce z URL na webu knihovny VUT(dspace.vutbr.cz) např.: 99999"

    # INFO
    urban_brief = "Vyhledávaní výrazu v urban slovníku"
    urban_help = f"`{prefix}urban výraz`\nPříklad:\n`{prefix}urban sure`"
    urban_not_found = "Pro daný výraz neexistuje záznam <:sadcat:576171980118687754>"

    weather_brief = "Vypíše informace o počasí ve zvoleném městě. Výchozí město je Brno."
    credit_limit_brief = "Vypíše, jak to funguje s ročním kreditovým stropem."
    credit_limit_info = """```cs
if ("pokazil jsem volitelný" or "Pokazil jsem aspoň 2 povinné")     \n  return 65
if ("Pokazil jsem 1 povinný" or "Mám průměr 2.0 nebo více než 2.0") \n  return 70
if ("Mám průměr pod 1.5")                                           \n  return 80
if ("Mám průměr pod 2.0")                                           \n  return 75
```"""

    # AUTOPIN
    autopin_max_pins_error = "Zprávu nelze připnout - byl dosažen maximální počet připnutých zpráv."
    autopin_add_brief = "Začne sledovat zprávu jako prioritní pin."
    autopin_add_done = "Prioritní pin nastaven."
    autopin_add_unknown_message = "Očekávána URL zprávy"
    autopin_remove_brief = "Odebere sledování prioritního pinu."
    autopin_remove_done = "Prioritní pin odebrán."
    autopin_remove_not_exists = "V kanálu {channel_name} není nastavena prioritní zpráva pro piny."
    autopin_no_messages = "Ještě neexistuje žádné mapování."
    autopin_list_brief = "Zobrazí všechny piny s nastavenou prioritou."
    autopin_list_unknown_channel = "> Neznámý kanál ({channel_id})"
    autopin_list_unknown_message = "> {channel} - Neznámá zpráva"
    autopin_list_item = "> {channel} - {url}"
    autopin_system_message = "Nelze připnout systémovou zprávu."
    autopin_list_info = "## Prioritní piny:"
    autopin_get_all_brief = "Získá všechny piny z kanálu a pošle je ve formátu markdown."
    autopin_no_pins = "V kanálu nejsou žádné piny."
    autopin_get_all_done = "Všechny piny z kanálu {channel_name} byly úspěšně staženy."

    # SYSTEM
    shutdown_brief = "Vypne bota"
    git_pull_brief = "Stáhne aktuálni změny z repa"

    uptime_brief = "Vypíše čas spuštění a čas uplynulý od spuštění"
    uptime_title = "Uptime"
    upsince_title = "Up since"
    uptime_latency = "Latency"
    longest_streak = "Longest streak without error"

    cogs_brief = "Vypíše seznam všech cogs a jejich stav"
    cog_is_loaded = "Toto rozšíření `{cog}` je již načtené."
    cog_unloaded = "Rozšíření `{cog}` odebráno."
    cog_loaded = "Rozšíření `{cog}` načteno."
    cog_is_unloaded = "Toto rozšíření `{cog}` není načteno"
    cog_not_unloadable = "Toto rozšíření `{cog}` je neodebratelné."
    cog_reloaded = "Rozšíření `{cog}` bylo načteno znovu."

    # DYNAMICCONFIG
    config_set_brief = "Nastaví hodnotu v konfiguraci"
    config_append_brief = "Přidá hodnotu do pole v konfiguraci"
    config_load_brief = "Znovu načte třídu ze souboru. Pro aplikování změn je potřeba znovu načíst i cog"
    config_list_brief = "Vypíše klíče konfigurace"
    config_get_brief = "Získá hodnotu z konfigurace"
    config_backup_brief = "Vytvoří záložní kopii konfigurace v novém souboru. Záloha bude obsahovat dnešní datum"
    config_sync_template_brief = "Přidá nové klíče z template do configu"
    config_updated = "Config updated."
    config_loaded = "Config loaded."
    config_wrong_key = "Nesprávný klíč"
    config_wrong_type = "Nesprávný typ"
    config_backup_created = "Config backup created."
    config_list_invalid_regex = "Chybný regex\n`{regex_err}`"
    config_synced = "Config successfully synchronized."

    # WEEK
    week_brief = "Vypíše, kolikátý je zrovna týden a jestli je sudý nebo lichý"
    week_warning = "Pro sudý/lichý se využívá kalendářní týden"

    # STREAMLINKS
    streamlinks_brief = "Úložiště všech streamů"
    streamlinks_add_brief = "Zapíše nový stream k předmětu"
    streamlinks_add_link_exists = "Tento stream již existuje."
    streamlinks_add_success = "Stream byl úspěšně přidán <:HYPERS:493154327318233088>"
    streamlinks_not_actual = "Tento seznam již není aktuální. Zavolej znovu příkaz pro aktualizaci."
    streamlinks_list_brief = "Vypíše zjednodušený seznam všech streamů k daném předmětu."
    streamlinks_no_stream = "K tomuto předmětu ještě neexistuje žádný stream."
    streamlinks_missing_description = "Nebyl zadán popis linku."
    streamlinks_remove_brief = "Smazání streamu z předmětu."
    streamlinks_ID = "ID se nachází v patičce embedu. Na konci v textu v závorce, kde je # (Jen to číslo je ID)."
    streamlinks_not_exists = "Stream s tímto ID nebyl nalezen."
    streamlinks_remove_prompt = "Opravdu chceš tento stream odstranit ({link})?"
    streamlinks_remove_success = "Stream <{link}> byl úspěšně smazán."
    streamlinks_date_format = "Formát `dd.mm.yyyy`. Bez zadání se bere datum u videa případně dnešní datum."
    streamlinks_invalid_link = "Neplatný odkaz na stream."
    streamlinks_update_brief = "Upraví stream z předmětu"
    streamlinks_update_success = "Stream byl úspěšně upraven <:HYPERS:493154327318233088>"
    streamlinks_update_nothing_to_change = "Není co měnit - je potřeba alespoň jeden volitelný argument"

    # LATEX
    latex_help = f"Příklad:\n`{prefix}latex [?fg=blue] x^n + y^n = z^n`"
    latex_desc = "Vykreslí LaTeX výraz"
    latex_colors = """**Možné barvy textu:**
    Transparent White Black Blue Cyan Green Magenta Red Yellow Orange Maroon NavyBlue RoyalBlue
    ProcessBlue SkyBlue Turquoise TealBlue Aquamarine BlueGreen Sepia Brown Tan Gray Fuchsia
    Lavender Purple Plum Violet GreenYellow Goldenrod Dandelion Apricot Peach Melon YellowOrange
    BurntOrange Bittersweet RedOrange Mahogany BrickRed OrangeRed RubineRed WildStrawberry Salmon
    CarnationPink VioletRed Rhodamine Mulberry RedViolet Thistle Orchid DarkOrchid RoyalPurple BlueViolet
    Periwinkle CadetBlue CornflowerBlue MidnightBlue Cerulean Emerald JungleGreen SeaGreen ForestGreen
    PineGreen LimeGreen YellowGreen SpringGreen OliveGreen RawSienna"""

    # STUDIJNI
    studijni_brief = "Úřední hodiny studijního Oddělení"
    studijni_web_error = "Chyba při parsování webu"
    studijni_office_hours = "Úřední hodiny"
    studijni_title = "C109 Studijní oddělení"

    # FITROOM
    fit_room_brief = "Zobrazení místnosti na plánku fakulty."
    fit_room_unreach = "Stránka s plánkem je nedostupná."
    fit_room_parsing_failed = "Načtení stránky s plánkem se nezdařilo. Nahlaš prosím tuto chybu správci bota."
    fit_room_room_not_on_plan = "Zadaná místnost {room} není na plánku nebo neexistuje."

    # MEME REPOST
    meme_repost_link = "[Odkaz na originál]({original_message_url}) v <#{original_channel}>"
    meme_leaderboard_brief = "#better-memes leaderboard"

    # EXAMS
    exams_brief = f"Zobrazí zkoušky pro daný ročník (výchozí ročník podle role)"
    exams_no_valid_role = "Nebyla nalezena ročníková role"
    exams_specify_year = "Specifikuj ročník"
    exams_no_valid_year = "Byl zadán neplatný ročník"
    exams_update_term_brief = "Aktualizuje termíny v kanálech termínů"
    exams_remove_all_terms_brief = "Odstraní termíny ze všech kanálů termínů"
    exams_remove_terms_brief = "Odstraní termíny ze zadaného kanálu"
    exams_start_terms_brief = "Zapne automatickou aktualizaci termínů"
    exams_stop_terms_brief = "Vypne automatickou aktualizaci termínů"
    exams_terms_updated = "`Termíny aktualizovány v {num_chan} kanálech`"
    exams_terms_removed = "`Termíny odstraněny`"
    exams_nothing_to_remove = "`Nenalezeny žádné termíny v kanálu {chan_name}`"
    exams_channel_is_not_text_channel = "`Nenalezeny žádné termíny v kanálu {chan_name}`"
    exams_automatic_update_started = "`Zapnuta automatická aktualizace termínů pro server: {guild_name}`"
    exams_automatic_update_stopped = "`Zastavena automatická aktualizace termínů pro server: {guild_name}`"

    # BOOKMARK
    bookmark_title = "Záložka na serveru {server}"
    blocked_bot = "Nemůžu ti posílat zprávy {user}"
    bookmark_created = "Záložka **{title_name}** vytvořena"
    bookmark_upload_limit = "Zpráva obsahuje přílohu přesahující upload limit, doporučuji si tuto přílohu stáhnout. V připadě smazání původní zprávy nebude příloha dostupná."

    # ICONS
    icon_ui = "UI pro přiřazení ikony"
    icon_set_success = "Změna ikony na {icon} proběhla úspěšně"
    icon_set_no_role = "Vstup neodpovídá žádné možné ikoně"
    icon_ui_choose = "Vyber si ikonu"
    icon_ui_fail = "Nastavit ikonu se nepodařilo"
    icon_ui_no_permission = "Na tuto ikonu nemáš právo"
    icon_removed = "Ikona byla odstraněna"

    # TIMEOUT COG
    timeout_brief = "Dočasně zakáže uživateli interakce na serveru."
    timeout_time = "Čas ve formátu dd.mm.yyyy nebo dd.mm.yyyy hh:mm. Základní jednotka je 1 hodina."
    timeout_reason = "Důvod dočasného umlčení uživatele."
    timeout_title = "{member} do {endtime} ({length})"
    timeout_field_text = "**Od:** {mod} | {starttime}\n**Navrácení:** {length}\n**Důvod:** {reason}"
    timeout_list_brief = "Vypíše uživatele se zatlumením."
    timeout_remove_brief = "Předčasně odebere umlčení uživateli."
    timeout_remove = "Umlčení zrušeno uživateli {user}."
    timeout_bad_format = "Neznamý formát času. Možné formáty:\n**3** - celé hodiny\n**0.5** - necelé hodiny, použij tečku\n**Datum konce:**\n{format}"
    timeout_permission = "Na umlčení **{user_list}** nemám práva."
    timeout_negative_time = "Čas nemůže být záporný."
    timeout_overflow = "Příliš velký počet hodin. Použij formát datumu."
    timeout_user_brief = "Použij tag uživatele/uživatelů"
    timeout_list_none = "Nenalezeny žádné umlčení."
    timeout_member_not_found = "{author} `{members}` jsem na serveru nenašel. Ujisti se, že jsi uživatele zadal správně pomocí @tag | name | ID."
    self_timeout = "Dočasně si zakážeš interakce na serveru"
    self_timeout_reason = "Sebeumlčení"
    self_timeout_success = "Sebeumlčení proběhlo úspěšně"

    # TIMEOUT WARS
    timeout_wars_user = "Uživatel {user} byl umlčen na {time:.0f} minut."
    timeout_wars_message_delete = "Uživatel {user} byl přistižen při mazání zpráv. Byl proto umlčen na {time:.0f} minut."
    timeout_wars_user_immunity = "Uživatel {user} má ještě imunitu na {time:.0f} sekund."

    # MODERATION
    slowmode_time = "Délka prodlevy v sekundách (vyber v autocomplete)"
    slowmode_set_brief = "Nastaví slowmode v aktuálním kanálu"
    slowmode_set_success = "Slowmode v kanálu {channel} nastaven na {delay} sekund."
    slowmode_remove_brief = "Vypne slowmode v aktuálním kanálu"
    slowmode_remove_success = "Slowmode v kanálu {channel} úspěšně odstraněn."

    # FUN COG
    fun_cat_brief = "Pošle náhodný obrázek kočky"
    fun_dog_brief = "Pošle náhodný obrázek psa"
    fun_fox_brief = "Pošle náhodný obrázek lišky"
    fun_duck_brief = "Pošle náhodný obrázek kachny"
    fun_dadjoke_brief = "Pošle náhodný dadjoke nebo vyhledá podle zadaného slova"
    fun_yo_mamajoke_brief = "Pošle náhodný Yo momma joke"
    fun_fuchs_brief = "Pošle náhodnou fuchs reakci"
    fun_fuchs_no_reaction = "Žádná fuchs reakce není k dispozici"

    # REPORT COG
    report_brief = "Systém pro reportování uživatelů nebo problémů na serveru"
    report_general_brief = "Nahlaš anonymně obecný problém moderátorům"
    report_google_form = "https://forms.gle/dkyb9eunjkJYTQdHA"
    report_google_form_brief = "Pošle odkaz na google form pro anonymní report"
    report_modal_placeholder = "Zadej důvod reportu"
    report_modal_success = "Report byl úspěšně odeslán"
    report_answer = "Zadej zprávu pro uživatele"
    report_answer_title = "Answer to report #{id}"
    report_answer_success = "Zpráva byla úspěšně odeslána"
    report_banned = "Bylo ti zakázáno posílat reporty z důvodu spamu falešných reportů. Pro další řešení kontaktuj moderátory"
    report_unban_user_brief = "Povolí uživateli posílat reporty"
    report_unban_user = "Uživatel {user} může opět posílat reporty"
    report_embed_answered = "### --- Last message ---\n{last_answer}\n\n### --- Current message ---\n\n{answer}"
    report_message_brief = "Nahlaš anonymně zprávu moderátorům"
    report_message_param = "Url zprávy nebo ID"
    report_message_embed = "### ---  Original message content ---\n{content}\n\n### --- Report reason ---\n\n{reason}"
    report_message_not_found = "Zpráva nebyla nalezena, zkontroluj že jsi dal správné url"
    report_message_already_deleted = "### Nahlášená zpráva byla už smazána @{author}"
    report_message_deleted = "### Nahlášená zpráva byla už smazána uživatelem @{author}"
    report_message_spam = "### Report #{id}, označen jako spam uživatelem @{author}"
    report_message_not_spam = "### Report #{id}, označení jako spam bylo zrušeno uživatelem @{author}"
    report_already_solved = "Report #{id} už byl uzavřen. V případě potřeby otevři další report"
    report_unresolved = "### Report #{id} was unresolved by @{author}"
    report_check_dm = "Odesílám report ..."
    report_files_too_big = "Soubory přesahující upload limit:\n- {files}"

    # SUBSCRIPTIONS COG
    subscription_add_brief = "Přidá odběr na vlákna se zvoleným tagem"
    subscription_remove_brief = "Zruší odběr na vlákna se zvoleným tagem"
    subscription_list_brief = "Zobrazí tvé odběry vláken"
    subscription_tag_not_found = "Pro zvolené fórum {channel} nebyl nalezen tag `{tag}`"
    subscription_added = "Odběr byl úspěšně nastaven pro {channel} s tagem `{tag}`"
    subscription_removed = "Odběr byl úspěšně odebrán pro {channel} s tagem `{tag}`"
    subscription_list_title = "Tvé odběry:"
    subscription_already_subscribed = "Tento odběr již máš nastaven"
    subscription_not_found = "Odběr s tímto tagem `{tag}` nebyl nalezen"
    subscription_embed_title = "Nový odebíraný příspěvek"
    subscription_embed_channel = "Příspěvek"
    subscription_embed_tags = "Tagy"
    subscription_embed_author = "Autor"

    # MESSAGE COG
    message_send_brief = "Pošle zprávu do kanálu"
    message_resend_brief = "Přepošle existující zprávu do kanálu"
    message_channel_brief = "Kanál, do kterého se má zpráva poslat"
    message_url_brief = "Url zprávy, která se má přeposlat"
    message_edit_brief = "Upraví existující zprávu"
    message_sent = "Zpráva byla odeslána do kanálu {channel}"
    message_not_found = "Zpráva nebyla nalezena"
    message_too_long = "Zpráva přesahuje limit 2000 znaků"
