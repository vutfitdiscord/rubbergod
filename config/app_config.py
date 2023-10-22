from datetime import timedelta
from typing import Dict, List

import toml


def get_attr(toml_dict: dict, section: str, attr_key: str):
    """
    Helper method for getting values from config override or config template.
    """
    try:
        return toml_dict[section][attr_key]
    except KeyError:
        return toml.load("config/config.template.toml", _dict=dict)[section][attr_key]


def eval_channels(toml_dict: dict, channels: list):
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

    toml_dict: dict = toml.load("config/config.toml", _dict=dict)

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
    verification_host_id: int = get_attr(toml_dict, "verification", "host_id")

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

    # Karma
    karma_ban_role_id: int = get_attr(toml_dict, "karma", "ban_role_id")
    karma_banned_channels: List[int] = get_attr(toml_dict, "karma", "banned_channels")
    karma_grillbot_leaderboard_size: int = get_attr(toml_dict, "karma", "grillbot_leaderboard_size")

    # Voting
    vote_minimum: int = get_attr(toml_dict, "vote", "minimum")
    vote_minutes: int = get_attr(toml_dict, "vote", "minutes")

    # ContestVote
    contest_vote_channel: int = get_attr(toml_dict, "contest_vote", "channel")
    contest_vote_weight_1: int = get_attr(toml_dict, "contest_vote", "weight_1")
    contest_vote_weight_2: int = get_attr(toml_dict, "contest_vote", "weight_1")
    contest_vote_weight_3: int = get_attr(toml_dict, "contest_vote", "weight_1")

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
    submod_helper_room: int = get_attr(toml_dict, "channels", "submod_helper_room")
    report_channel: int = get_attr(toml_dict, "channels", "report_channel")

    # Meme repost
    meme_room: int = get_attr(toml_dict, "meme_repost", "meme_room")
    meme_repost_room: int = get_attr(toml_dict, "meme_repost", "meme_repost_room")
    repost_threshold: int = get_attr(toml_dict, "meme_repost", "repost_threshold")
    meme_repost_image_extensions: list = get_attr(toml_dict, "meme_repost", "image_extensions")

    # Bot rooms
    allowed_channels: List[int] = eval_channels(
        toml_dict, get_attr(toml_dict, "channels", "allowed_channels")
    )

    # Roles
    role_channels: List[int] = get_attr(toml_dict, "role", "channels")

    # Subjects and reviews
    review_forbidden_roles: List[int] = get_attr(toml_dict, "review", "forbidden_roles")
    subject_bit_id: int = get_attr(toml_dict, "review", "bit_id")
    subject_mit_id_start: int = get_attr(toml_dict, "review", "mit_id_start")
    subject_mit_id_end: int = get_attr(toml_dict, "review", "mit_id_end")
    subject_mit_id_rnd: List[int] = get_attr(toml_dict, "review", "mit_id_rnd")

    # memes
    hug_emojis: List[str] = get_attr(toml_dict, "meme", "hug_emojis")
    upgraded_pocitani_thread_id: int = get_attr(toml_dict, "meme", "upgraded_pocitani_thread_id")
    upgraded_pocitani_start_num: int = get_attr(toml_dict, "meme", "upgraded_pocitani_start_num")

    # uh oh
    uhoh_string: str = get_attr(toml_dict, "meme", "uhoh_string")

    # grillbot
    grillbot_ids: List[int] = get_attr(toml_dict, "grillbot", "ids")
    grillbot_api_url: str = get_attr(toml_dict, "grillbot", "api_url")
    grillbot_api_supported_methods: List[str] = get_attr(toml_dict, "grillbot", "api_supported_methods")
    grillbot_api_key: str = get_attr(toml_dict, "grillbot", "api_key")
    grillbot_api_karma_sync_interval: int = get_attr(toml_dict, "grillbot", "karma_sync_interval")

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
    ios_channel_id: int = get_attr(toml_dict, "util", "ios_channel_id")

    # exams
    exams_page_size: int = get_attr(toml_dict, "exams", "page_size")
    exams_paginator_duration: int = get_attr(toml_dict, "exams", "paginator_duration")
    exams_term_channels: List[str] = get_attr(toml_dict, "exams", "term_channels")
    exams_terms_update_interval: float = get_attr(toml_dict, "exams", "terms_update_interval")
    exams_subscribe_default_guild: bool = get_attr(toml_dict, "exams", "subscribe_default_guild")

    # room check
    enable_room_check: bool = get_attr(toml_dict, "random", "enable_room_check")

    # icons
    icon_roles: List[int] = get_attr(toml_dict, "icons", "icon_roles")
    icon_role_prefix: str = get_attr(toml_dict, "icons", "role_prefix")
    icon_rules: Dict[int, Dict[str, List[int]]] = {
        int(k): v for k, v in get_attr(toml_dict, "icons", "rule").items()
    }
    icon_ui_cooldown: float = get_attr(toml_dict, "icons", "ui_cooldown")

    # timeout wars
    timeout_wars_reaction_count: int = get_attr(toml_dict, "timeout_wars", "reaction_count")
    timeout_wars_log_channel: int = get_attr(toml_dict, "timeout_wars", "log_channel")
    timeout_wars_immunity_time: timedelta = timedelta(
        minutes=get_attr(toml_dict, "timeout_wars", "immunity_time")
    )
    timeout_wars_timeout_time: timedelta = timedelta(
        minutes=get_attr(toml_dict, "timeout_wars", "timeout_time")
    )
    timeout_wars_chance_all_mute: int = get_attr(toml_dict, "timeout_wars", "chance_all_mute")
    timeout_wars_chance_random_mute: int = get_attr(toml_dict, "timeout_wars", "chance_random_mute")

    # forum
    forum_tags: List[str] = get_attr(toml_dict, "forum", "tags")
    forum_autoclose_forums: List[int] = get_attr(toml_dict, "forum", "autoclose_forums")


config = Config()


def config_get_keys() -> list:
    keys = []
    for key in Config.__dict__.keys():
        if not key.startswith('__') and key not in config.config_static:  # Remove builtin attributes
            keys.append(key)
    return keys


def load_config():
    global config
    config = Config()
