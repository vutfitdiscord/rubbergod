import re

import disnake

from rubbergod import Rubbergod


def generate_mention(user_id: int) -> str:
    return f"<@{user_id}>"


def has_role(user: disnake.Member, role_name: str) -> bool:
    """Check if user has specific role by name"""
    return role_name.lower() in [x.name.lower() for x in user.roles]


async def get_users_from_tag(bot: Rubbergod, tag: str) -> list[disnake.User]:
    """get user(s) object(s) from tag(s), return list of user(s)"""
    users = []
    # regex to match global name or nickname
    user_ids = re.findall(r"<@[!]?\d+>", tag)
    for user in user_ids:
        user = re.search(r"\d+", user)
        user = await bot.get_or_fetch_user(int(user.group()))
        users.append(user)
    return users


async def get_members_from_tag(guild: disnake.Guild, tag: str) -> list[disnake.Member]:
    """get member(s) object(s) from tag(s), return list of member(s)"""
    members = []
    # regex to match global name or nickname
    member_ids = re.findall(r"<@[!]?\d+>", tag)
    for member in member_ids:
        member = re.search(r"\d+", member)
        member = await guild.get_or_fetch_member(int(member.group()))
        if member is None:
            continue
        members.append(member)
    return members
