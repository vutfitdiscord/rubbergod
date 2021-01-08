import discord
from discord.ext import commands

import utils
from config.app_config import Config

# TODO: use messages
from config.messages import Messages
from repository import role_group_repo

group_repo = role_group_repo.RoleGroupRepository()


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

    async def hadle_reaction(self, ctx):
        role_data = await self.get_join_role_data(ctx["message"])
        for line in role_data:
            if str(ctx["emoji"]) == line[1]:
                await self.add_perms(line[0], ctx["member"], ctx["guild"])
                break
        else:
            await ctx["message"].remove_reaction(ctx["emoji"], ctx["member"])

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        ctx = await utils.reaction_get_ctx(self.bot, payload)
        if ctx is None:
            return

        if ctx["channel"].id in Config.role_channels:
            role_data = await self.get_join_role_data(ctx["message"])
            for line in role_data:
                if str(ctx["emoji"]) == line[1]:
                    await self.remove_perms(line[0], ctx["member"], ctx["guild"])
                    break

    # Returns list of role names and emotes that represent them
    async def get_join_role_data(self, message):
        input_string = message.content
        input_string = input_string.replace("**", "")
        try:
            input_string = input_string.rstrip().split("\n")
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
                    msg = utils.fill_message(
                        "role_invalid_line", user=message.author.id, line=discord.utils.escape_mentions(line)
                    )
                    await message.channel.send(msg)
        for line in output:
            if "<#" in line[0] or "<@" in line[0]:
                line[0] = line[0].replace("<#", "")
                line[0] = line[0].replace("<@&", "")
                line[0] = line[0].replace("<@", "")
                line[0] = line[0].replace(">", "")
                try:
                    line[0] = int(line[0])
                except Exception:
                    if message.channel.id not in Config.role_channels:
                        msg = utils.fill_message(
                            "role_invalid_line",
                            user=message.author.id,
                            line=discord.utils.escape_mentions(line[0]),
                        )
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
            roles, channels = self.get_target(line[0], guild)
            if roles == [None] and channels == [None]:
                msg = utils.fill_message(
                    "role_not_role", user=message.author.id, not_role=discord.utils.escape_mentions(line[0])
                )
                await message.channel.send(msg)
            else:
                try:
                    await message.add_reaction(line[1])
                except discord.errors.HTTPException:
                    msg = utils.fill_message(
                        "role_invalid_emote",
                        user=message.author.id,
                        not_emote=discord.utils.escape_mentions(line[1]),
                        role=discord.utils.escape_mentions(line[0]),
                    )
                    await message.channel.send(msg)

    async def add_perms(self, target, member, guild):
        """Add a target role / channel to a member."""
        roles, channels = self.get_target(target, guild)
        for role in roles:
            if role is not None and role not in member.roles:
                await member.add_roles(role)
        for channel in channels:
            if channel is not None:
                perms: discord.PermissionOverwrite = channel.overwrites_for(member)

                if not perms.is_empty():
                    deny_exp_perm = discord.Permissions()
                    deny_exp_perm.view_channel = True

                    perm_pair = perms.pair()
                    if deny_exp_perm.value == perm_pair[1].value and perm_pair[0].value == 0:
                        # User have only expected permission (Allow: None, Deny: view_channel).
                        # This configuration will remove overwrite before checks and set.
                        # This will prevent from removing higher permissions from channels (or bans).
                        await channel.set_permissions(member, overwrite=None)

                perms_for: discord.Permissions = channel.permissions_for(member)
                if perms_for.administrator or perms_for.view_channel:  # Is mod, or now have access. Ignore
                    continue

                if not perms.is_empty():
                    perms.read_messages = True
                    await channel.set_permissions(member, overwrite=perms)
                else:
                    await channel.set_permissions(member, read_messages=True)

    async def remove_perms(self, target, member, guild):
        """Remove a target role / channel from a member."""
        roles, channels = self.get_target(target, guild)
        for role in roles:
            if role is not None and role in member.roles:
                await member.remove_roles(role)
        for channel in channels:
            if channel is not None:
                perms_for: discord.Permissions = channel.permissions_for(member)
                if perms_for.administrator:  # Is useless create overwrite if user is moderator.
                    continue

                perms = channel.overwrites_for(member)
                if perms is not None:
                    perms.read_messages = False
                    await channel.set_permissions(member, overwrite=perms)
                else:
                    await channel.set_permissions(member, read_messages=False)

    def get_target(self, target, guild):
        """Detect if target is a channel a role or a group."""
        # Try a group first
        group = group_repo.get_group(target)
        if group is not None:
            roles, channels = [], []
            for role_id in group.role_ids:
                roles.append(discord.utils.get(guild.roles, id=int(role_id)))
            for channel_id in group.channel_ids:
                channels.append(discord.utils.get(guild.channels, id=int(channel_id)))
            return roles, channels

        # if ID
        if isinstance(target, int) or target.isdigit():
            role = discord.utils.get(guild.roles, id=int(target))
            channel = discord.utils.get(guild.channels, id=int(target))
        # else if name of role / #channel
        else:
            role = discord.utils.get(guild.roles, name=target)
            channel = discord.utils.get(guild.channels, name=target[1:].lower())

        return [role], [channel]


class RolesGroupManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def add_group(self, ctx, name: str):
        group_repo.add_group(name)
        await ctx.send(f"Pridal jsem groupu {name}")

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def get_group(self, ctx, name: str):
        group = group_repo.get_group(name)
        channels = ", ".join([f"<#{channel_id}>" for channel_id in group.channel_ids])
        await ctx.send(f"Jmeno: {group.name}\n" f"Channel IDs: {channels}\n" f"Role IDs:{group.role_ids}")

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def groups(self, ctx):
        names = group_repo.group_names()
        for name in names:
            await ctx.send(name)

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def add_channel_id(self, ctx, name: str, channel_id: int):
        group_repo.group_add_channel_id(name, channel_id)
        await ctx.send("Done")

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def add_role_id(self, ctx, name: str, role_id: int):
        group_repo.group_add_role_id(name, role_id)
        await ctx.send("Done")

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def group_reset_channels(self, ctx, name: str):
        group_repo.group_reset_channels(name)
        await ctx.send("Done")

    @commands.check(utils.is_bot_admin)
    @commands.command()
    async def group_reset_roles(self, ctx, name: str):
        group_repo.group_reset_roles(name)
        await ctx.send("Done")


class ChannelManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.check(utils.is_bot_admin)
    @commands.group()
    async def channel(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(Messages.channel_help)

    @channel.command(aliases=["cp"])
    async def copy(self, ctx, src: discord.TextChannel, dst: discord.TextChannel):
        """
        Copy permissions from src channel to dst.
        Both channels are expected as tags or IDs
        """
        for key in src.overwrites:
            await dst.set_permissions(key, overwrite=src.overwrites[key])
        await ctx.send(Messages.channel_copy_done)

    @channel.command()
    async def clone(self, ctx, src: discord.TextChannel, name):
        """Clone channel with same permissions as src."""
        new = await src.clone(name=name)
        await ctx.send(utils.fill_message("channel_clone_done", id=new.id))

    @copy.error
    @clone.error
    async def error(self, ctx, error):
        """Print help on missing argument"""
        if isinstance(error, commands.MissingRequiredArgument):
            if "copy" in ctx.invoked_subcommand.name:
                await ctx.send(Messages.channel_copy_help)
            elif "clone" in ctx.invoked_subcommand.name:
                await ctx.send(Messages.channel_clone_help)


def setup(bot):
    bot.add_cog(ReactToRole(bot))
    bot.add_cog(RolesGroupManager(bot))
    bot.add_cog(ChannelManager(bot))
