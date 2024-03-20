from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    add_brief = "Přidá odběr na vlákna se zvoleným tagem"
    remove_brief = "Zruší odběr na vlákna se zvoleným tagem"
    list_brief = "Zobrazí tvé odběry vláken"
    tag_not_found = "Pro zvolené fórum {channel} nebyl nalezen tag `{tag}`"
    subscription_added = "Odběr byl úspěšně nastaven pro {channel} s tagem `{tag}`"
    subscription_removed = "Odběr byl úspěšně odebrán pro {channel} s tagem `{tag}`"
    subscription_not_found = "Odběr s tímto tagem `{tag}` nebyl nalezen"
    list_title = "Tvé odběry:"
    already_subscribed = "Tento odběr již máš nastaven"
    embed_title = "Nový odebíraný příspěvek"
    embed_channel = "Příspěvek"
    embed_tags = "Tagy"
    embed_author = "Autor"
