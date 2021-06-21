from typing import List
import toml


toml_dict: dict = toml.load("config/config.toml", _dict=dict)


def get_attr(section: str, attr_key: str):
    """
    Helper method for getting values from config override or config template.
    """
    try:
        return toml_dict[section][attr_key]
    except KeyError:
        return toml.load("config/config.template.toml", _dict=dict)[section][attr_key]


def eval_channels(channels: list):
    """
    Evaluate channel 'config variable name' to ID
    """
    for idx, channel_name in enumerate(channels):
        if isinstance(channel_name, str):
            channels[idx] = get_attr("channels", channel_name)
    return channels


class Config:
    """
    Wrapper class for Config and config template.\n
    It checks value from config override and if not exists that will be take from config template.
    """

    # String representation of toml config
    toml_dict = toml_dict

    # Authorization
    key: str = get_attr("base", "key")

    # Base information
    admin_ids: List[int] = get_attr("base", "admin_ids")
    guild_id: int = get_attr("base", "guild_id")

    # Database
    db_string: str = get_attr("database", "db_string")

    # Base bot behavior
    command_prefix: tuple = tuple(get_attr("base", "command_prefix"))
    default_prefix: str = get_attr("base", "default_prefix")
    ignored_prefixes: tuple = tuple(get_attr("base", "ignored_prefixes"))

    # Role IDs
    mod_role: int = get_attr("base", "mod_role")
    submod_role: int = get_attr("base", "submod_role")
    helper_role: int = get_attr("base", "helper_role")

    # Verification
    verification_role: str = get_attr("verification", "role")
    verification_role_id: int = get_attr("verification", "role_id")

    # Verification email sender settings
    email_name: str = get_attr("email", "name")
    email_addr: str = get_attr("email", "addr")
    email_smtp_server: str = get_attr("email", "smtp_server")
    email_smtp_port: str = get_attr("email", "smtp_port")
    email_pass: str = get_attr("email", "pass")

    # Extensions loaded on bot start
    extensions: List[str] = get_attr("cogs", "extensions")

    # Config: static values -> cannot be got/set by command
    config_static: List[str] = get_attr("config", "static")

    # Roll dice
    max_dice_at_once: int = get_attr("random", "max_dice_at_once")
    dice_before_collation: int = get_attr("random", "dice_before_collation")
    max_dice_groups: int = get_attr("random", "max_dice_groups")
    max_dice_sides: int = get_attr("random", "max_dice_sides")
    enable_room_check: bool = get_attr("random", "enable_room_check")

    # Karma
    karma_ban_role_id: int = get_attr("karma", "ban_role_id")
    karma_banned_channels: List[int] = get_attr("karma", "banned_channels")
    karma_grillbot_leaderboard_size: int = get_attr("karma", "grillbot_leaderboard_size")

    # Voting
    vote_minimum: int = get_attr("vote", "minimum")
    vote_minutes: int = get_attr("vote", "minutes")

    # Pin emoji count to pin
    autopin_count: int = get_attr("autopin", "count")
    autopin_banned_channels: List[int] = get_attr("autopin", "banned_channels")
    autopin_banned_users: List[int] = get_attr("autopin", "banned_users")
    autopin_warning_cooldown: int = get_attr("autopin", "warning_cooldown")

    # Special channel IDs
    log_channel: int = get_attr("channels", "log_channel")
    bot_dev_channel: int = get_attr("channels", "bot_dev_channel")
    vote_room: int = get_attr("channels", "vote_room")
    bot_room: int = get_attr("channels", "bot_room")
    mod_room: int = get_attr("channels", "mod_room")

    # Bot rooms
    allowed_channels: List[int] = eval_channels(get_attr("channels", "allowed_channels"))

    # Roles
    role_channels: List[int] = get_attr("role", "channels")

    # Subjects shortcuts
    subjects: List[str] = get_attr("review", "subjects")
    review_forbidden_roles: List[int] = get_attr("review", "forbidden_roles")

    # How many roles a user needs to have to be considered a rolehoarder
    rolehoarder_default_limit: int = get_attr("rolehoarder", "default_limit")

    # memes
    hug_emojis: List[str] = get_attr("meme", "hug_emojis")
    covid_channel_id: str = get_attr("meme", "covid_channel_id")
    storno_delay: int = get_attr("meme", "storno_delay")

    # Arcas
    arcas_id: int = get_attr("meme", "arcas_id")
    arcas_delay: int = get_attr("meme", "arcas_delay")  # Value is in hours
    # uh oh
    uhoh_string: str = get_attr("meme", "uhoh_string")

    # grillbot
    grillbot_id: int = get_attr("grillbot", "id")

    # weather token to openweather API
    weather_token: str = get_attr("weather", "token")

    # warden
    duplicate_limit: int = get_attr("warden", "duplicate_limit")
    deduplication_channels: List[int] = get_attr("warden", "deduplication_channels")

    # week command
    starting_week: int = get_attr("week", "starting_week")

    # absolvent
    bc_role_id: int = get_attr("absolvent", "bc_role_id")
    ing_role_id: int = get_attr("absolvent", "ing_role_id")

    # Emotes
    emote_loading: str = get_attr("emote", "loading")

    # util
    ios_looptime_minutes: int = get_attr("util", "ios_looptime_minutes")

    # subscriptions
    unsubscribable_channels: list = get_attr("subscriptions", "unsubscribable_channels")
