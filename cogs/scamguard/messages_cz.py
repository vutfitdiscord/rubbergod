from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    scam_detected_title = "🚨 Detekován MrBeast crypto scam"
    scam_detected_description = (
        "{user} (`{user_name}`) poslal v {channel} obrázky odpovídající známému "
        "MrBeast crypto scam spamu. Zpráva byla automaticky smazána."
    )
    scam_detected_hint = (
        "Pokud jde o napadený účet, proveď ban → unban pro smazání nedávných zpráv "
        "napříč celým serverem. Pokud je to falešný poplach, tlačítko ignoruj."
    )
    scam_ban_unban_button = "Ban → Unban (smazat zprávy)"
    scam_ban_unban_done = "Provedl {author}: ban → unban pro {user}, zprávy za posledních {hours}h smazány."
    scam_ban_unban_forbidden = "Nemám oprávnění banovat {user}."
    scam_ban_unban_failed = "Ban → unban pro {user} selhal: {error}"
