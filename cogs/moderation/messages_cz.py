from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    time_param = "Délka prodlevy mezi zprávami v sekundách"
    set_brief = "Nastaví slowmode v aktuálním kanálu"
    set_success = "Slowmode v kanálu {channel} nastaven na {delay} sekund."
    remove_brief = "Vypne slowmode v aktuálním kanálu"
    remove_success = "Slowmode v kanálu {channel} úspěšně odstraněn."

    moderation_log = "### {action_emoji} {target.mention} `{target.id}` was {action}\n" \
                    "- {timestamp}\n" \
                    "- Given By: {entry.user.mention} `{entry.user.id}`\n" \
                    "- Reason: `{entry.reason}`"
