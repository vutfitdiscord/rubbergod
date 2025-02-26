from prometheus_client import Counter, Gauge

METRIC_PREFIX = "discord_"

COMMANDS_GAUGE = Gauge(METRIC_PREFIX + "stat_total_commands", "Number of commands")

USER_GAUGE = Gauge(METRIC_PREFIX + "stat_total_users", "Number of users this bot can see")

CONNECTION_GAUGE = Gauge(
    METRIC_PREFIX + "connected",
    "Determines if the bot is connected to Discord",
    ["shard"],
)

LATENCY_GAUGE = Gauge(
    METRIC_PREFIX + "latency",
    "latency to Discord",
    ["shard"],
    unit="seconds",
)

ON_INTERACTION_COUNTER = Counter(
    METRIC_PREFIX + "event_on_interaction",
    "Number of interactions called by users",
    ["shard", "interaction", "guild", "command"],
)

ON_COMMAND_COUNTER = Counter(
    METRIC_PREFIX + "event_on_command",
    "Number of commands called by users",
    ["shard", "guild", "command"],
)

GUILD_GAUGE = Gauge(METRIC_PREFIX + "stat_total_guilds", "Number of guilds this bot is a member of")

CHANNEL_GAUGE = Gauge(
    METRIC_PREFIX + "stat_total_channels",
    "Number of channels this bot is has access to",
)

METRICS = [
    COMMANDS_GAUGE,
    USER_GAUGE,
    CONNECTION_GAUGE,
    LATENCY_GAUGE,
    ON_INTERACTION_COUNTER,
    ON_COMMAND_COUNTER,
    GUILD_GAUGE,
    CHANNEL_GAUGE,
]
