from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    role_invalid_line = "{user}, řádek `{line}` je neplatný."
    role_format = "{user}, použij `!god`."
    role_not_on_server = "Nepíšeš na serveru, takže předpokládám, že myslíš role VUT FIT serveru."
    role_not_role = "{user}, {not_role} není role."
    role_invalid_emote = "{user}, {not_emote} pro roli {role} není emote."
    role_channel_copy_brief = "Zkopíruje opravnění z jednoho kanálu na druhý"
    role_channel_clone_brief = "Naklonuje kanál"
    role_channel_create_brief = "Vytvoří privátní text kanál pro uživatele s konkrétní role."

    role_create_start = "Migrace oprávnění na roli pro **{role}**"
    role_create_progress = "Migrace pro #{channel} • uživatelů: {perms} {progress}"
    role_create_done = "Migrace oprávnění na roli **{role}** dokončena. Počet oprávnění: {perms}"
    role_migration_allert = "Přidání/Odebrání **{channel}** bude trvat déle než je obvyklé (až 30 min)." \
                            "Prosím o strpení. Opakované klikání na reakce nemá vliv na dobu zpracování přístupu."

    remove_exclusive_roles = "Odstraní konflikty rolí, kdy má uživatel více exkluzivních rolí."
    remove_exclusive_roles_start = "Probíhá odstraňování konfliktů rolí {role1} a {role2}"
    role_no_exlusives = "Nebyly nalezeny žádné konflikty rolí"
    remove_exclusive_roles_done = "Úspěšně odstraněny konflikty rolí"
    role_to_remove_param = "Role, která se má odstranit"

    channel_copy_start = "Probíhá kopírování kanálu"
    channel_copy_done = "Práva byla zkopírována."
    channel_clone_start = "Probíhá klonování kanálu"
    channel_clone_done = "Kanál <#{id}> byl vytvořen."
    channel_create_start = "Probíhá vytváření kanálu"
    channel_create_done = "Vytvoření kanálu bylo úspěšné, kanál {channel} vytvořen s přístupem pro roli **{role}**.\n • Počet overwrites: **{perms}**"
    channel_rate_param = "Po kolika částech aktualizovat progress bar."
    channel_get_overwrites_brief = "Vypíše počet přístupových práv pro všechny mistnosti"
    channel_get_overwrites_start = "Probíhá získávání přístupových práv"
    channel_get_overwrites_done = "Získávání přístupových práv bylo úspěšné"
    channel_role_to_overwrites_brief = "Vytvoří roli z přístupových práv"
    channel_role_to_overwrites_start = "Probíhá převádění role na přístupová práva"
    channel_role_to_overwrites_done = "Role úspěšně převedena na přístupová práva"
    channel_overwrites_to_role_brief = "Vytvoří overwrites na místnost z role"
    channel_overwrites_to_role_start = "Probíhá převádění přístupových práv na roli"
    channel_overwrites_to_role_done = "Přístupová práva byla úspěšně převedena na roli"
