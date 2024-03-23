from config.app_config import config
from features.callable_string import Formatable


class Messages(metaclass=Formatable):
    # GENERAL MESSAGES
    prefix = config.default_prefix

    server_warning = "Tohle funguje jen na VUT FIT serveru."

    karma_get_missing = "Toaster pls, měl jsi bordel v DB. Musel jsem za tebe uklidit."

    on_ready_message = "<:peepowave:693070888546861096>"
    cooldown = "Příliš rychle, zkus to znovu za {time:.3}s"
    embed_not_author = "Hraj si na svém písečku s tebou zavolanými příkazy. <:pepeGun:826943455032901643>"
    base_leaderboard_format_str = "_{position}._ - **{member_name}**:"
    invalid_time_format = "Neplatný formát času.\n{time_format}."
    time_format = "Formát: `dd.mm.yyyy [HH:MM]` nebo `1(w)eek 2(M)onth 3(d)ay 4(h)our 5(m)inute 6(s)econd`"
    attachment_too_big = "Příloha je příliš velká. Maximální velikost je 25 MB."
    api_error = "Nepovedlo se získat data z API\n{error}"
    message_not_found = "Zpráva nebyla nalezena. Zkontroluj formát."
    blocked_bot = "Nemůžu ti posílat zprávy {user}"
    trash_delete_id = "trash:delete"   # global identifier for delete button

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
    fitwide_update_db_brief = "Aktualizuje databázi s loginy"
    fitwide_update_db_start = "Aktualizuji databázi..."
    fitwide_new_logins = "Našel jsem {new_logins} nových loginů."
    fitwide_update_db_done = "Aktualizace databáze proběhla úspěšně."
    fitwide_db_debug = "Debug: Našel jsem {cnt_new} nových prvaků."
    fitwide_pull_db_brief = "Stáhne databázi uživatelů na merlinovi"
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
    fitwide_vutapi_brief = "Získá data z VUT API"

    # ERROR
    moved_command = "Tento příkaz již není v textové formě podporován. Příkaz byl nahrazen příkazem </{name}:{id}>"
    command_timed_out = "Příkaz nereagoval a byl nečekaně ukončen."
    command_invoke_error = "Došlo k nečekané chybě, už na tom pracujeme <:notLikeRubbergod:1112395455142314044>"
    user_input_error = "Chyba ve vstupu, jestli vstup obsahuje `\"`, nahraď je za `'`"
    spamming = "{user} Nespamuj tolik <:sadcat:576171980118687754>, příkaz můžeš použít až za {time}."
    member_not_found = "{member} Nikoho takového jsem na serveru nenašel."
    user_not_found = "{user} Nikoho takového jsem nenašel."

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

    # VERIFY
    verify_brief = "Ověření studenta pro přístup na server."
    verify_login_parameter = "Přihlašovací FIT login (`xlogin00`), osobní 6 místné VUT číslo nebo MUNI UČO."
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
    verify_step_done = "{user} Tímto krokem jsi už prošel. ({admin} pls)"
    verify_invalid_channel = "Tento příkaz je možné spustit pouze v DMs nebo na VUT FIT serveru."
    invalid_login = "{user} Neplatný login. Přečti si prosím <#591386755547136020>. ({admin} pls)"
    verify_subject = "FIT Discord verifikace"
    dynamic_verify_requested = "Byla zaslána žádost o verifikaci. Vyčkej prosím než ji někdo z oprávněných osob schválí."
    dynamic_verify_declined = "Tvá žádost o verifikaci byla zamítnuta."
    dynamic_verify_create_brief = "Vytvoření pravidla pro verifikaci"
    dynamic_verify_edit_brief = "Upravení pravidla pro verifikaci"
    dynamic_verify_list_brief = "Zobrazení pravidel pro verifikaci"
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
        "/diplom <Titul.> <Jméno> <Příjmení> <Číslo diplomu> <ID kvalifikační práce, poslední kombinace čísel v kolonce URI na webu knihovny VUT <http://hdl.handle.net/11012/19121> >\n" \
        "např: Bc. Josef Novák 123456/2019 99999\n" \
        "(při <http://hdl.handle.net/11012/99999>)\n" \
        "Údaje slouží k jednorázovému ověření a nejsou nikam ukládány."
    absolvent_degree_param = "Dosažený titul - Bc./Ing."
    absolvent_name_param = "Křestní jméno např.: Josef"
    absolvent_surname_param = "Příjmení např.: Novák"
    absolvent_diploma_param = "Číslo diplomu např.: 123456/2019"
    absolvent_thesis_id_param = "poslední kombinace čísel v URI kolonce na webu knihovny VUT(dspace.vut.cz) např.: 99999"
    absolvent_not_on_server = "{user}, na použití tohoto příkazu musíš být na FIT VUT serveru.\nhttps://discord.gg/vutfit"
    absolvent_status_thesis = "Ověřuji práci..."
    absolvent_status_diploma = "Ověřuji diplom..."
    absolvent_status_roles = "Přidávam role..."

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
    system_get_logs_brief = "Získá logy bota z journalctl"
    system_get_logs_lines_brief = "Počet řádků, které se mají zobrazit"

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

    # MEME REPOST
    meme_repost_link = "[Odkaz na originál]({original_message_url}) v <#{original_channel}>"
    meme_leaderboard_brief = "#better-memes leaderboard"
    upgraded_pocitani_caught_deleting = "Podvádět mazáním zpráv je zakázáno. Začínáme znovu: "

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

    # TIMEOUT WARS
    timeout_wars_user = "Uživatel {user} byl umlčen na {time:.0f} minut."
    timeout_wars_message_delete = "Uživatel {user} byl přistižen při mazání zpráv. Byl proto umlčen na {time:.0f} minut."
    timeout_wars_user_immunity = "Uživatel {user} má ještě imunitu na {time:.0f} sekund."
