import discord
from discord.ext import commands

import utils
from config.app_config import Config
from config.messages import Messages
from repository import roles_group_repo

group_repo = roles_group_repo.RoleGroupRepository()

class ReactToRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id in Config.role_channels:
            role_data = await self.get_join_role_data(message)
            await self.message_role_reactions(message, role_data)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        ctx = await utils.reaction_get_ctx(self.bot, payload)
        if ctx is None:
            return

        if ctx['channel'].id in Config.role_channels:
            role_data = await self.get_join_role_data(ctx['message'])
            for line in role_data:
                if str(ctx['emoji']) == line[1]:
                    await self.add_role_on_reaction(line[0],
                                                    ctx['member'],
                                                    ctx['guild'])
                    break
            else:
                await ctx['message'].remove_reaction(ctx['emoji'], ctx['member'])

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        ctx = await utils.reaction_get_ctx(self.bot, payload)
        if ctx is None:
            return

        if ctx['channel'].id in Config.role_channels:
            role_data = await self.get_join_role_data(ctx['message'])
            for line in role_data:
                if str(ctx['emoji']) == line[1]:
                    await self.remove_role_on_reaction(line[0],
                                                       ctx['member'],
                                                       ctx['guild'])
                    break

    # Returns list of role names and emotes that represent them
    async def get_join_role_data(self, message):
        input_string = message.content
        input_string = input_string.replace("**", "")
        try:
            input_string = input_string.rstrip().split('\n')
        except ValueError:
            await message.channel.send(utils.fill_message("role_format", user=message.author.id))
            return None
        output = []
        for line in input_string:
            try:
                out = line.split(" - ", 1)[0].split()
                out = [out[1], out[0]]
                output.append(out)
            except Exception:
                if message.channel.id not in Config.role_channels:
                    msg = utils.fill_message("role_invalid_line",
                                             user=message.author.id,
                                             line=discord.utils.escape_mentions(line))
                    await message.channel.send(msg)
        for line in output:
            if "<#" in line[0]:
                line[0] = line[0].replace("<#", "")
                line[0] = line[0].replace(">", "")
                try:
                    line[0] = int(line[0])
                except Exception:
                    if message.channel.id not in Config.role_channels:
                        msg = utils.fill_message("role_invalid_line",
                                                 user=message.author.id,
                                                 line=discord.utils.escape_mentions(line[0]))
                        await message.channel.send(msg)
        return output

    # Adds reactions to message
    async def message_role_reactions(self, message, data):
        if message.channel.type is not discord.ChannelType.text:
            await message.channel.send(Messages.role_not_on_server)
            guild = self.bot.get_guild(Config.guild_id)
        else:
            guild = message.guild
        for line in data:
            not_role = discord.utils.get(guild.roles, name=line[0]) is None
            if isinstance(line[0], int) or line[0].isdigit():
                not_channel = discord.utils.get(guild.channels, id=int(line[0])) is None
            else:
                not_channel = line[0][0] != "#" or\
                    discord.utils.get(guild.channels, name=line[0][1:].lower()) is None
            if not_role and not_channel:
                msg = utils.fill_message("role_not_role",
                                         user=message.author.id,
                                         not_role=discord.utils.escape_mentions(line[0]))
                await message.channel.send(msg)
            else:
                try:
                    await message.add_reaction(line[1])
                except discord.errors.HTTPException:
                    msg = utils.fill_message("role_invalid_emote",
                                             user=message.author.id,
                                             not_emote=discord.utils.escape_mentions(line[1]),
                                             role=discord.utils.escape_mentions(line[0]))
                    await message.channel.send(msg)

    async def add_perms(self, target, member, guild):
        """Add a target role / channel to a member."""
        roles, channels = self.get_target(target, guild)
        for roles in roles:
            if role is not None and role not in member.roles:
                await member.add_roles(role)
        for channel in channels:
            if channel is not None:
                await channel.set_permissions(member, read_messages=True)

    async def remove_perms(self, target, member, guild):
        """Remove a target role / channel from a member."""
        role, channel = self.get_target(target, guild)
        if role is not None:
            if role in member.roles:
                await member.remove_roles(role)
        elif channel is not None:
            await channel.set_permissions(member, read_messages=False)
        return

    async def get_target(self, target, guild):
        """Detect if target is a channel a role or a group."""
        # Try a group first
        group = group_repo.get_group(target)
        if group is not None:
            roles, channels = [], []
            for role_id in group.role_ids:
                roles.append(discord.utils.get(guild.roles,
                                               id=target))
            for channel_id in group.channel_ids:
                channels.append(discord.utils.get(guild.channels,
                                                  id=target))
            return roles, channels

        # Check for a role
        role = discord.utils.get(guild.roles,
                                 name=target)
        if role is not None:
            return [role], []

        # Not a role, check for a channel mention
        try:
            channel = discord.utils.get(guild.channels, id=int(target))
        except ValueError:
            channel = None
        if channel is None:
            # not a channel mention, try again with a channel name
            channel = discord.utils.get(guild.channels, name=target[1:].lower())
        return [], [channel]


class RolesGroupManager(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def is_admin(ctx):
        return ctx.author.id == config.admin_id

    @commands.check(is_admin)
    @commands.command()
    async def add_group(self, ctx, name: str):
        group_repo.add_group(name)
        ctx.send(f"Pridal jsem groupu {name}")

    @commands.check(is_admin)
    @commands.command()
    async def get_group(self, ctx, name: str):
        group = group_repo.get_group(name)
        ctx.send(f"Jmeno: {group.name}\n"
                 f"Channel IDs:{group.channel_ids}\n"
                 f"Role IDs:{group.role_ids}")

    @commands.check(is_admin)
    @commands.command()
    async def add_channel_id(self, ctx, name: str, channel_id: int):
        group_repo.group_add_channel_id(name, channel_id)
        ctx.send(f"Done")

    @commands.check(is_admin)
    @commands.command()
    async def add_role_id(self, ctx, name: str, role_id: int):
        group_repo.group_add_role_id(name, role_id)
        ctx.send(f"Done")

    @commands.check(is_admin)
    @commands.command()
    async def group_reset_channels(self, ctx, name: str):
        group_repo.group_reset_channels(name)
        ctx.send(f"Done")

    @commands.check(is_admin)
    @commands.command()
    async def group_reset_roles(self, ctx, name: str):
        group_repo.group_reset_roles(name)
        ctx.send(f"Done")


def setup(bot):
    bot.add_cog(ReactToRole(bot))
    bot.add_cog(RolesGroupManager(bot))
