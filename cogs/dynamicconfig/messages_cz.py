from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    set_brief = "Nastaví hodnotu v konfiguraci"
    append_brief = "Přidá hodnotu do pole v konfiguraci"
    load_brief = "Znovu načte třídu ze souboru. Pro aplikování změn je potřeba znovu načíst i cog"
    list_brief = "Vypíše klíče konfigurace"
    get_brief = "Získá hodnotu z konfigurace"
    sync_template_brief = "Přidá nové klíče z template do konfigurace"
    wrong_key = "Nesprávný klíč"
    wrong_type = "Nesprávný typ"
    list_invalid_regex = "Chybný regex\n`{regex_err}`"
    config_updated = "Konfigurace aktualizována."
    config_loaded = "Konfigurace načtena."
