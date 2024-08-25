from disnake.ext import commands


def short_cooldown(f):
    """5x/20s"""
    return commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)(f)


def default_cooldown(f):
    """5x/30s"""
    return commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)(f)


def long_cooldown(f):
    """1x/20s"""
    return commands.cooldown(rate=1, per=20.0, type=commands.BucketType.user)(f)
