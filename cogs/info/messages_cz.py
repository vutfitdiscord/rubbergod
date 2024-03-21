from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    urban_brief = "Vyhledávaní výrazu v urban slovníku"
    urban_not_found = "Pro daný výraz neexistuje záznam <:sadcat:576171980118687754>"

    weather_brief = "Vypíše informace o počasí ve zvoleném městě. Výchozí město je Brno."
    credit_limit_brief = "Vypíše, jak to funguje s ročním kreditovým stropem."
    credit_limit_info = """```cs
if ("pokazil jsem volitelný" or "Pokazil jsem aspoň 2 povinné")     \n  return 65
if ("Pokazil jsem 1 povinný" or "Mám průměr 2.0 nebo více než 2.0") \n  return 70
if ("Mám průměr pod 1.5")                                           \n  return 80
if ("Mám průměr pod 2.0")                                           \n  return 75
```"""
