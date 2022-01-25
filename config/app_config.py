from typing import List
import toml

def get_attr(toml_dict:dict, section: str, attr_key: str):
    """
    Helper method for getting values from config override or config template.
    """
    try:
        return toml_dict[section][attr_key]
    except KeyError:
        return toml.load("config/config.template.toml", _dict=dict)[section][attr_key]


def eval_channels(toml_dict:dict, channels: list):
    """
    Evaluate channel 'config variable name' to ID
    """
    for idx, channel_name in enumerate(channels):
        if isinstance(channel_name, str):
            channels[idx] = get_attr(toml_dict, "channels", channel_name)
    return channels


class Config:
    """
    Wrapper class for Config and config template.\n
    It checks value from config override and if not exists that will be take from config template.
    """

    toml_dict:dict = toml.load("config/config.toml", _dict=dict)

    # Authorization
    key: str = get_attr(toml_dict, "base", "key")

    # Base information
    admin_ids: List[int] = get_attr(toml_dict, "base", "admin_ids")
    guild_id: int = get_attr(toml_dict, "base", "guild_id")

    # Database
    db_string: str = get_attr(toml_dict, "database", "db_string")

    # Base bot behavior
    command_prefix: tuple = tuple(get_attr(toml_dict, "base", "command_prefix"))
    default_prefix: str = get_attr(toml_dict, "base", "default_prefix")
    ignored_prefixes: tuple = tuple(get_attr(toml_dict, "base", "ignored_prefixes"))

    # Role IDs
    mod_role: int = get_attr(toml_dict, "base", "mod_role")
    submod_role: int = get_attr(toml_dict, "base", "submod_role")
    helper_role: int = get_attr(toml_dict, "base", "helper_role")

    # Verification
    verification_role: str = get_attr(toml_dict, "verification", "role")
    verification_role_id: int = get_attr(toml_dict, "verification", "role_id")

    # Verification email sender settings
    email_name: str = get_attr(toml_dict, "email", "name")
    email_addr: str = get_attr(toml_dict, "email", "addr")
    email_smtp_server: str = get_attr(toml_dict, "email", "smtp_server")
    email_smtp_port: str = get_attr(toml_dict, "email", "smtp_port")
    email_pass: str = get_attr(toml_dict, "email", "pass")

    # Extensions loaded on bot start
    extensions: List[str] = get_attr(toml_dict, "cogs", "extensions")

    # Config: static values -> cannot be got/set by command
    config_static: List[str] = get_attr(toml_dict, "config", "static")

    # Roll dice
    max_dice_at_once: int = get_attr(toml_dict, "random", "max_dice_at_once")
    dice_before_collation: int = get_attr(toml_dict, "random", "dice_before_collation")
    max_dice_groups: int = get_attr(toml_dict, "random", "max_dice_groups")
    max_dice_sides: int = get_attr(toml_dict, "random", "max_dice_sides")
    enable_room_check: bool = get_attr(toml_dict, "random", "enable_room_check")

    # Karma
    karma_ban_role_id: int = get_attr(toml_dict, "karma", "ban_role_id")
    karma_banned_channels: List[int] = get_attr(toml_dict, "karma", "banned_channels")
    karma_grillbot_leaderboard_size: int = get_attr(toml_dict, "karma", "grillbot_leaderboard_size")

    # Voting
    vote_minimum: int = get_attr(toml_dict, "vote", "minimum")
    vote_minutes: int = get_attr(toml_dict, "vote", "minutes")

    # Pin emoji count to pin
    autopin_count: int = get_attr(toml_dict, "autopin", "count")
    autopin_banned_channels: List[int] = get_attr(toml_dict, "autopin", "banned_channels")
    autopin_banned_users: List[int] = get_attr(toml_dict, "autopin", "banned_users")
    autopin_warning_cooldown: int = get_attr(toml_dict, "autopin", "warning_cooldown")

    # Special channel IDs
    log_channel: int = get_attr(toml_dict, "channels", "log_channel")
    bot_dev_channel: int = get_attr(toml_dict, "channels", "bot_dev_channel")
    vote_room: int = get_attr(toml_dict, "channels", "vote_room")
    bot_room: int = get_attr(toml_dict, "channels", "bot_room")
    mod_room: int = get_attr(toml_dict, "channels", "mod_room")

    # Meme repost
    meme_room: int = get_attr(toml_dict, "meme_repost", "meme_room")
    meme_repost_room: int = get_attr(toml_dict, "meme_repost", "meme_repost_room")
    repost_threshold: int = get_attr(toml_dict, "meme_repost", "repost_threshold")
    meme_repost_image_extensions: list = get_attr(toml_dict, "meme_repost", "image_extensions")

    # Bot rooms
    allowed_channels: List[int] = eval_channels(toml_dict, get_attr(toml_dict, "channels", "allowed_channels"))

    # Roles
    role_channels: List[int] = get_attr(toml_dict, "role", "channels")

    # Subjects shortcuts
    subjects: List[str] = get_attr(toml_dict, "review", "subjects")
    review_forbidden_roles: List[int] = get_attr(toml_dict, "review", "forbidden_roles")

    # How many roles a user needs to have to be considered a rolehoarder
    rolehoarder_default_limit: int = get_attr(toml_dict, "rolehoarder", "default_limit")

    # memes
    hug_emojis: List[str] = get_attr(toml_dict, "meme", "hug_emojis")
    covid_channel_id: str = get_attr(toml_dict, "meme", "covid_channel_id")
    storno_delay: int = get_attr(toml_dict, "meme", "storno_delay")

    # Arcas
    arcas_id: int = get_attr(toml_dict, "meme", "arcas_id")
    arcas_delay: int = get_attr(toml_dict, "meme", "arcas_delay")  # Value is in hours
    # uh oh
    uhoh_string: str = get_attr(toml_dict, "meme", "uhoh_string")

    # grillbot
    grillbot_id: int = get_attr(toml_dict, "grillbot", "id")

    # weather token to openweather API
    weather_token: str = get_attr(toml_dict, "weather", "token")

    # warden
    duplicate_limit: int = get_attr(toml_dict, "warden", "duplicate_limit")
    deduplication_channels: List[int] = get_attr(toml_dict, "warden", "deduplication_channels")
    repost_ignore_users: List[int] = get_attr(toml_dict, "warden", "repost_ignore_users")

    # week command
    starting_week: int = get_attr(toml_dict, "week", "starting_week")

    # absolvent
    bc_role_id: int = get_attr(toml_dict, "absolvent", "bc_role_id")
    ing_role_id: int = get_attr(toml_dict, "absolvent", "ing_role_id")

    # Emotes
    emote_loading: str = get_attr(toml_dict, "emote", "loading")

    # util
    ios_looptime_minutes: int = get_attr(toml_dict, "util", "ios_looptime_minutes")

    # subscriptions
    subscribable_channels: list = get_attr(toml_dict, "subscriptions", "subscribable_channels")

    # exams
    exams_page_size:int = get_attr(toml_dict, "exams", "page_size")
    exams_paginator_duration = get_attr(toml_dict, "exams", "paginator_duration")

config = Config()

def load_config():
    global config
    config = Config()
