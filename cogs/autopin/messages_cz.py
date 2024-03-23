from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    max_pins_error = "Zprávu nelze připnout - byl dosažen maximální počet připnutých zpráv."
    add_brief = "Začne sledovat zprávu jako prioritní pin."
    add_done = "Prioritní pin nastaven."
    add_unknown_message = "Očekávána URL zprávy"
    remove_brief = "Odebere sledování prioritního pinu."
    remove_done = "Prioritní pin odebrán."
    remove_not_exists = "V kanálu {channel_name} není nastavena prioritní zpráva pro piny."
    no_messages = "Ještě neexistuje žádné mapování."
    list_brief = "Zobrazí všechny piny s nastavenou prioritou."
    list_unknown_channel = "> Neznámý kanál ({channel_id})"
    list_unknown_message = "> {channel} - Neznámá zpráva"
    list_item = "> {channel} - {url}"
    system_message = "Nelze připnout systémovou zprávu."
    list_info = "## Prioritní piny:"
    get_all_brief = "Získá všechny piny z kanálu a pošle je ve formátu markdown."
    no_pins = "V kanálu nejsou žádné piny."
    get_all_done = "Všechny piny z kanálu {channel_name} byly úspěšně staženy."
