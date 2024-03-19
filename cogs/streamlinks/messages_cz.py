from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    streamlinks_brief = "Úložiště všech streamů"
    add_brief = "Zapíše nový stream k předmětu"
    add_link_exists = "Tento stream již existuje."
    add_success = "Stream byl úspěšně přidán <:HYPERS:493154327318233088>"
    not_actual = "Tento seznam již není aktuální. Zavolej znovu příkaz pro aktualizaci."
    list_brief = "Vypíše zjednodušený seznam všech streamů k daném předmětu."
    no_stream = "K tomuto předmětu ještě neexistuje žádný stream."
    missing_description = "Nebyl zadán popis linku."
    remove_brief = "Smazání streamu z předmětu."
    id_description = "ID se nachází v patičce embedu. Na konci v textu v závorce, kde je # (Jen to číslo je ID)."
    not_exists = "Stream s tímto ID nebyl nalezen."
    remove_prompt = "Opravdu chceš tento stream odstranit ({link})?"
    remove_success = "Stream <{link}> byl úspěšně smazán."
    date_format = "Formát `dd.mm.yyyy`. Bez zadání se bere datum u videa případně dnešní datum."
    invalid_link = "Neplatný odkaz na stream."
    update_brief = "Upraví stream z předmětu"
    update_success = "Stream byl úspěšně upraven <:HYPERS:493154327318233088>"
    update_nothing_to_change = "Není co měnit - je potřeba alespoň jeden volitelný argument"
