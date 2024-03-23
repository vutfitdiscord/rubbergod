from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    time_param = "Délka prodlevy v sekundách (vyber v autocomplete)"
    set_brief = "Nastaví slowmode v aktuálním kanálu"
    set_success = "Slowmode v kanálu {channel} nastaven na {delay} sekund."
    remove_brief = "Vypne slowmode v aktuálním kanálu"
    remove_success = "Slowmode v kanálu {channel} úspěšně odstraněn."
