from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    urban_brief = "Vyhledávaní výrazu v urban slovníku"
    urban_not_found = "Pro daný výraz neexistuje záznam <:sadcat:576171980118687754>"

    credit_limit_brief = "Vypíše, jak to funguje s ročním kreditovým stropem."
    credit_limit_info = """```cs
if ("pokazil jsem volitelný" or "Pokazil jsem aspoň 2 povinné")     \n  return 65
if ("Pokazil jsem 1 povinný" or "Mám průměr 2.0 nebo více než 2.0") \n  return 70
if ("Mám průměr pod 1.5")                                           \n  return 80
if ("Mám průměr pod 2.0")                                           \n  return 75
```"""

    # Weather / Počasí
    weather_brief = "Vypíše informace o počasí ve zvoleném městě. Výchozí město je Brno."
    weather_description = "Aktuální počasí v městě {city}, {country}"
    invalid_name = "Takhle se žádné město určitě nejmenuje."
    city_not_found = "Město nenalezeno"
    token_error = "Rip token -> Rebel pls fix"
    no_city = "Město nenalezeno! <:pepeGun:484470874246742018> ({result})"
    weather = "Počasí"
    temperature = "Teplota"
    feels_like = "Pocitová teplota"
    humidity = "Vlhkost"
    wind = "Vítr"
    clouds = "Oblačnost"
    visibility = "Viditelnost"

    nasa_image_brief = "Pošle obrázek dne z NASA"
    nasa_image_error = "Nepovedlo se stáhnout obrázek z NASA"
    nasa_url = "https://apod.nasa.gov/apod/astropix.html"
