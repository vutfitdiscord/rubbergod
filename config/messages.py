from config.app_config import config
from features.callable_string import Formatable


class Messages(metaclass=Formatable):
    # GENERAL MESSAGES
    prefix = config.default_prefix
    rubbergod_url = "https://github.com/vutfitdiscord/rubbergod"

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

    # MEME
    upgraded_pocitani_caught_deleting = "Podvádět mazáním zpráv je zakázáno. Začínáme znovu: "
