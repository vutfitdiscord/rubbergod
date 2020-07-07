from typing import List

import config.config as ConfigOverride

import importlib.util
template_spec = importlib.util.spec_from_file_location('module.name', 'config/config.template.py')
config_template = importlib.util.module_from_spec(template_spec)
template_spec.loader.exec_module(config_template)


def get_attr(attr_key: str):
    """
    Helper method for getting values from config override or config template.
    """
    if not hasattr(ConfigOverride.Config, attr_key):
        return getattr(config_template.Config, attr_key)

    return getattr(ConfigOverride.Config, attr_key)


class Config:
    """
    Wrapper class for Config and config template.\n
    It checks value from config override and if not exists that will be take from config template.
    """

    # Authorization
    key: str = get_attr('key')

    # Verification
    verification_role: str = get_attr('verification_role')
    verification_role_id: int = get_attr('verification_role_id')

    # Base information
    admin_id: int = get_attr('admin_id')
    guild_id: int = get_attr('guild_id')

    # Verification email sender settings
    email_name: str = get_attr('email_name')
    email_addr: str = get_attr('email_addr')
    email_smtp_server: str = get_attr('email_smtp_server')
    email_smtp_port: str = get_attr('email_smtp_port')
    email_pass: str = get_attr('email_pass')

    # Database
    db_string: str = get_attr('db_string')

    # Base bot behavior
    command_prefix: tuple = get_attr('command_prefix')
    default_prefix: str = get_attr('default_prefix')
    ignored_prefixes: tuple = get_attr('ignored_prefixes')

    # Extensions loaded on bot start
    extensions: List[str] = get_attr('extensions')

    # Roll dice
    max_dice_at_once: int = get_attr('max_dice_at_once')
    dice_before_collation: int = get_attr('dice_before_collation')
    max_dice_groups: int = get_attr('max_dice_groups')
    max_dice_sides: int = get_attr('max_dice_sides')

    # Karma
    karma_ban_role_id: int = get_attr('karma_ban_role_id')
    karma_banned_channels: List[int] = get_attr('karma_banned_channels')
    grillbot_leaderboard_size : int = get_attr('grillbot_leaderboard_size')

    # Voting
    vote_minimum: int = get_attr('vote_minimum')
    vote_minutes: int = get_attr('vote_minutes')

    # Pin emoji count to pin
    pin_count: int = get_attr('pin_count')
    pin_banned_channels: List[int] = get_attr('pin_banned_channels')

    # Special channel IDs
    log_channel: int = get_attr('log_channel')
    bot_dev_channel: int = get_attr('bot_dev_channel')
    vote_room: int = get_attr('vote_room')
    bot_room: int = get_attr('bot_room')
    mod_room: int = get_attr('mod_room')

    # Bot rooms
    allowed_channels: List[int] = get_attr('allowed_channels')

    # String constants
    role_string: str = get_attr('role_string')
    role_channels: List[int] = get_attr('role_channels')
    hug_emojis: List[str] = get_attr('hug_emojis')

    # Subjects shortcuts
    subjects: List[str] = get_attr('subjects')
    reviews_forbidden_roles: List[int] = get_attr('reviews_forbidden_roles')

    # How many people to print if the limit argument is not specified
    rolehoarder_default_limit: int = get_attr('rolehoarder_default_limit')

    # Arcas
    arcas_id: int = get_attr('arcas_id')
    arcas_delay: int = get_attr('arcas_delay')  # Value is in hours

    # uh oh
    uhoh_string: str = get_attr('uhoh_string')

    # grillbot
    grillbot_id: int = get_attr('grillbot_id')

    # weather token to openweather API
    weather_token: str = get_attr('weather_token')

    # warden
    duplicate_limit: int = get_attr('duplicate_limit')
    deduplication_channels: List[int] = get_attr('deduplication_channels')

    # week command
    starting_week: int = get_attr('starting_week')
