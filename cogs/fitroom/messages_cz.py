from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    room_brief = "Zobrazení místnosti na plánku fakulty."
    room_unreach = "Stránka s plánkem je nedostupná."
    parsing_failed = "Načtení stránky s plánkem se nezdařilo. Nahlaš prosím tuto chybu správci bota."
    room_not_on_plan = "Zadaná místnost {room} není na plánku nebo neexistuje."
