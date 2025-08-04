from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    wrong_diploma_format = "Chybný formát čísla diplomu! Př: 123456/2019"
    wrong_name = "Nepovedla se ověřit shoda zadaného jména s tvým předchozím záznamem o studiu na FIT VUT."
    thesis_not_found_error = "Práce dle zadaného ID nebyla na webu nalezena."
    web_error = "Nepovedlo se ověřit obhájení kvalifikační práce pod uvedeným číslem na webu, jménem, typem práce a rokem obhájení (dle čísla diplomu)."
    diploma_error = "Diplom (číslo a jméno) se nepovedlo na webu ověřit."
    diplom_success = "Diplom byl úspěšně ověřen. <:vutEZ:1276989323509760001>"
    id_from_help = "Zadej svoje ID práce."
    diplom_brief = "Příkaz pro ověření absolvování studia na FIT VUT"
    diplom_help_brief = "Vypíše help k příkazu /diplom"
    not_in_db = "Tvůj login nebyl nalezen v databázi ověřených uživatelů. Použij příkaz `/verify` pro ověření (je zapotřebí školní email)."
    not_verified = "Pro zavolání tohoto příkazu je potřeba se ověřit pomocí příkazu `/verify`."
    diplom_help_print = f"{diplom_brief} - zadejte CASE-SENSITIVE údaje ve formátu:\n" \
        "/diplom <Titul.> <Jméno> <Příjmení> <Číslo diplomu> <ID kvalifikační práce, poslední kombinace čísel v kolonce URI na webu knihovny VUT <http://hdl.handle.net/11012/19121> >\n" \
        "např: Bc. Josef Novák 123456/2019 99999\n" \
        "(při <http://hdl.handle.net/11012/99999>)\n" \
        "Údaje slouží k jednorázovému ověření a nejsou nikam ukládány."
    degree_param = "Dosažený titul - Bc./Ing."
    name_param = "Křestní jméno např.: Josef"
    surname_param = "Příjmení např.: Novák"
    diploma_param = "Číslo diplomu např.: 123456/2019"
    thesis_id_param = "poslední kombinace čísel v URI kolonce na webu knihovny VUT(dspace.vut.cz) např.: 99999"
    not_on_server = "{user}, na použití tohoto příkazu musíš být na FIT VUT serveru.\nhttps://discord.gg/vutfit"
    status_thesis = "Ověřuji práci <a:loading:1276977394405871657>"
    status_diploma = "Ověřuji diplom <a:loading:1276977394405871657>"
    status_roles = "Přidávám role <a:loading:1276977394405871657>"
