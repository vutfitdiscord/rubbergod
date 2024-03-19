from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    roll_brief = "Vygeneruje náhodné celé číslo z intervalu <**first**, **second**>"
    flip_brief = "Hodí mincí"
    pick_brief = "Vybere jedno ze slov za otazníkem."
    pick_format = "*Is foo bar? Yes No Maybe*"
    pick_empty = "Nenapsal jsi žádné možnosti k otázce."

    rng_generator_format = f"Použití: `{GlobalMessages.prefix}roll x [y]`\n" \
                           "rozmezí x, y jsou celá čísla,\n" \
                           "pokud y není specifikováno, " \
                           "je považováno za 0."
