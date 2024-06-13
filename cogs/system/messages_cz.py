from config.messages import Messages as GlobalMessages


class MessagesCZ(GlobalMessages):
    shutdown_brief = "Vypne bota"
    git_pull_brief = "Stáhne aktuálni změny z repa"
    get_logs_brief = "Získá logy bota z journalctl"
    lines_param = "Počet řádků, které se mají zobrazit"
    service_param = "Název služby"

    uptime_brief = "Vypíše čas spuštění a čas uplynulý od spuštění"
    uptime_title = "Doba od spuštění"
    upsince_title = "Spuštěno"
    longest_streak = "Nejdelší doba bez chyby"

    cogs_brief = "Vypíše seznam všech cogs a jejich stav"
    embed_title = "Informace o rozšířeních"
    embed_description = "```✅ Loaded ({loaded}) / ❌ Unloaded ({unloaded}) / 🔄 All ({all})```"
    cog_is_loaded = "Rozšíření `{cog}` je již načtené."
    cog_is_unloaded = "Rozšíření `{cog}` není načteno"
    cog_not_unloadable = "Rozšíření `{cog}` je neodebratelné."
    success_load = "Rozšíření `{cog}` načteno."
    success_unload = "Rozšíření `{cog}` odebráno."
    success_reload = "Rozšíření `{cog}` bylo načteno znovu."
    override = "📄 Tučné položky jsou rozdílné oproti config.extension"

    rubbergod_brief = "Vypíše základní informace o botovi"
    commands_count = "Celkový počet - **{sum}**\nTextové příkazy - **{context}**\nSlash příkazy - **{slash}**\nUser příkazy - **{user_comm}**\nMessage příkazy - **{message_comm}**"
    latency = "Odezva"
    guilds = "Počet serverů"
    commands = "Příkazy"
