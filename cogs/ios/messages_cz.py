from config.messages import Messages as GlobalMessages
from config.app_config import config


class MessagesCZ(GlobalMessages):
    ios_brief = "Připomene všem prasatům, že si mají jít po sobě uklidit"
    task_start_brief = "Začne pravidelně připomínat všem prasatům, že si mají jít po sobě uklidit"
    task_start_success = f"Automatické připomínání úspěšně nastaveno. Bude se od teď provádět každých {config.ios_looptime_minutes} minut."
    task_start_already_set = "Automatické připomínání už je nastaveno."
    task_stop_brief = "Zastaví automatické připomínání"
    task_stop_success = "Automatické připomínání zastaveno."
    task_nothing_to_stop = "Automatické připomínání není nastaveno."
    task_cancel_brief = "Okamžitě ukončí automatické připomínání (přeruší aktuální běh)"
    parsing_error = "Keizzho, máš bordel v parsování."
    howto_clean = "Pokud nevíte, jak po sobě uklidit, checkněte: https://discordapp.com/channels/461541385204400138/534431057001316362/698701631495340033"
