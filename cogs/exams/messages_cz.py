from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    exams_brief = "Zobrazí zkoušky pro daný ročník (výchozí ročník podle role)"
    no_valid_role = "Nebyla nalezena ročníková role"
    specify_year = "Specifikuj ročník"
    no_valid_year = "Byl zadán neplatný ročník"
    update_term_brief = "Aktualizuje termíny v kanálech termínů"
    remove_all_terms_brief = "Odstraní termíny ze všech kanálů termínů"
    remove_terms_brief = "Odstraní termíny ze zadaného kanálu"
    start_terms_brief = "Zapne automatickou aktualizaci termínů"
    stop_terms_brief = "Vypne automatickou aktualizaci termínů"
    terms_updated = "`Termíny aktualizovány v {num_chan} kanálech`"
    terms_removed = "`Termíny odstraněny`"
    nothing_to_remove = "`Nenalezeny žádné termíny v kanálu {chan_name}`"
    channel_is_not_text_channel = "`Nenalezeny žádné termíny v kanálu {chan_name}`"
    automatic_update_started = "`Zapnuta automatická aktualizace termínů pro server: {guild_name}`"
    automatic_update_stopped = "`Zastavena automatická aktualizace termínů pro server: {guild_name}`"
