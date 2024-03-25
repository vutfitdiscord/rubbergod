from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    shutdown_brief = "Vypne bota"
    git_pull_brief = "Stáhne aktuálni změny z repa"
    get_logs_brief = "Získá logy bota z journalctl"
    lines_param = "Počet řádků, které se mají zobrazit"

    uptime_brief = "Vypíše čas spuštění a čas uplynulý od spuštění"
    uptime_title = "Uptime"
    upsince_title = "Up since"
    uptime_latency = "Latency"
    longest_streak = "Longest streak without error"

    cogs_brief = "Vypíše seznam všech cogs a jejich stav"
    cog_is_loaded = "Toto rozšíření `{cog}` je již načtené."
    cog_unloaded = "Rozšíření `{cog}` odebráno."
    cog_loaded = "Rozšíření `{cog}` načteno."
    cog_is_unloaded = "Toto rozšíření `{cog}` není načteno"
    cog_not_unloadable = "Toto rozšíření `{cog}` je neodebratelné."
    cog_reloaded = "Rozšíření `{cog}` bylo načteno znovu."
