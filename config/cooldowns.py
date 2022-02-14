from disnake.ext import commands

# 5x/20s
def short_cooldown(f):
    return commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)(f)

# 5x/30s
def default_cooldown(f):
    return commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)(f)

# 1x/20s
def long_cooldown(f):
    return commands.cooldown(rate=1, per=20.0, type=commands.BucketType.user)(f)
