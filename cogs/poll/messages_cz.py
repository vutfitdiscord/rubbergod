from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    basic_brief = "Zahájí hlasování, s vlastními možnostmi."
    boolean_brief = "Zahájí hlasování, s možnostmi Ano, Ne. Pouze 1 hlas na uživatele."
    opinion_brief = "Zahájí hlasování, s možnostmi Souhlasím, Neutral, Nesouhlasím. Pouze 1 hlas na uživatele."
    list_brief = "Vypíše všechna hlasování"
    already_voted = "Pro možnost **{option}** jsi již hlasoval"
    closed = "Hlasování s názvem **{title}** bylo ukončeno. {url}\n"
    winning_option = "Vyhrála možnost\n{option} - {votes} hlasů ({percentage}%)"
    tie_options = "Remíza mezi možnostmi {options}"
    embed_description = (
        "{description}\n- Počet hlasů na uživatele: {votes}\n- Konec: {date}\n- "
        "Anonymní hlasování: {anonymous}\n- Celkový počet hlasů: {all_votes}"
    )
    not_author = "Toto hlasování nemůžeš ukončit, protože nejsi jeho autorem."
    title_param = "Otázka v hlasování"
    description_param = "Popis nebo další informace k hlasování"
    attachment_param = "Přidat obrázek/video k hlasování"
    anonymous_param = "Anonymní hlasování. Při neanonymním hlasování lze vypsat kdo pro co hlasoval"
    voted = "Hlasoval jsi pro možnost **{option}**"
    vote_removed = "Zrušil jsi své hlasování v\n## [{title}]({url})\n"
    end_short = "Konec hlasování je přílíš krátký. Minimální délka je 5 minut."
    end_long = "Konec hlasování je přílíš dlouhý. Maximální délka je 1 rok."
    not_found = "Hlasování nebylo nalezeno."
    not_voted = "Nehlasoval jsi pro žádnou možnost."
    button_spam = "Nespamuj prosím. Počkej {time}, aby jsi mohl pokračovat."
    no_active_polls = "Nebylo nalezeno žádné aktivní hlasování."
    is_anonymous = "Hlasování je anonymní. Nelze zobrazit hlasy."
    list_polls = "**ID: {id} | {url} ** - {title}\n"
