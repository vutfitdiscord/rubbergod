"""
Cog implementing channels and roles management. Copying/creating channels with permissions.
"""

import asyncio
import io
from typing import List, Tuple

import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
# TODO: use messages for prints
from config.messages import Messages
from database.review import SubjectDetailsDB
from database.role_group import RoleGroupDB
from features.reaction_context import ReactionContext
from permissions import permission_check


class Roles(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.lock = asyncio.Lock()

    # Returns list of role names and emotes that represent them
    async def get_join_role_data(self, message):
        input_string = message.content
        input_string = input_string.replace("**", "")
        try:
            input_string = input_string.rstrip().split("\n")
        except ValueError:
            await message.channel.send(Messages.role_format(user=message.author.id))
            return None
        output = []
        for line in input_string:
            try:
                out = line.split(" - ", 1)[0].split()
                out = [out[1], out[0]]
                output.append(out)
            except Exception:
                if message.channel.id not in self.config.role_channels:
                    msg = Messages.role_invalid_line(user=message.author.id,
                                                     line=disnake.utils.escape_mentions(line))
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
                    if message.channel.id not in self.config.role_channels:
                        msg = Messages.role_invalid_line(
                            user=message.author.id,
                            line=disnake.utils.escape_mentions(line[0]),
                        )
                        await message.channel.send(msg)
        return output

    # Adds reactions to message
    async def message_role_reactions(self, message, data):
        if message.channel.type is not disnake.ChannelType.text:
            await message.channel.send(Messages.role_not_on_server)
            guild = self.bot.get_guild(self.config.guild_id)
        else:
            guild = message.guild
        for line in data:
            roles, channels = self.get_target(line[0], guild)
            if roles == [None] and channels == [None]:
                msg = Messages.role_not_role(
                    user=message.author.id,
                    not_role=disnake.utils.escape_mentions(line[0])
                )
                await message.channel.send(msg)
            else:
                try:
                    await message.add_reaction(line[1])
                except disnake.errors.HTTPException:
                    msg = Messages.role_invalid_emote(
                        user=message.author.id,
                        not_emote=disnake.utils.escape_mentions(line[1]),
                        role=disnake.utils.escape_mentions(line[0]),
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
                perms: disnake.PermissionOverwrite = channel.overwrites_for(member)

                if not perms.is_empty():
                    deny_exp_perm = disnake.Permissions()
                    deny_exp_perm.view_channel = True

                    perm_pair = perms.pair()
                    if deny_exp_perm.value == perm_pair[1].value and perm_pair[0].value == 0:
                        # User have only expected permission (Allow: None, Deny: view_channel).
                        # This configuration will remove overwrite before checks and set.
                        # This will prevent from removing higher permissions from channels (or bans).
                        await channel.set_permissions(member, overwrite=None)

                perms_for: disnake.Permissions = channel.permissions_for(member)
                if perms_for.administrator or perms_for.view_channel:  # Is mod, or now have access. Ignore
                    continue

                total_overwrites = len(channel.overwrites)
                if total_overwrites >= 490:
                    await member.send(Messages.role_migration_allert(channel=channel))
                    async with self.lock:
                        role = disnake.utils.get(guild.roles, name=channel.name)
                        if not role:
                            role = await self.create_role(channel)
                        await member.add_roles(role)
                else:
                    current_perms = channel.permissions_for(member)
                    if not current_perms.read_messages:
                        if not perms.is_empty():
                            perms.read_messages = True
                            await channel.set_permissions(member, overwrite=perms)
                        else:
                            await channel.set_permissions(member, read_messages=True)

    async def create_role(self, channel: disnake.abc.GuildChannel, ignore: disnake.Member = None):
        """Create a new role with the same name as channel name and transfer permissions"""
        keep = {}  # users and roles with special permission other then default read
        # prepare default permission for comparison
        default_perm = disnake.PermissionOverwrite()
        default_perm.view_channel = True
        total_overwrites = len(channel.overwrites)
        rate = 50
        guild = self.bot.get_guild(self.config.guild_id)
        role = await guild.create_role(name=channel.name)
        message = await self.bot_dev_channel.send(Messages.role_create_start(role=role.name))
        for idx, item in enumerate(channel.overwrites):
            if type(item) == disnake.Member:
                if ignore and ignore.id == item.id:
                    pass
                elif channel.overwrites[item] != default_perm:
                    keep[item] = channel.overwrites[item]
                else:
                    await item.add_roles(role)
            else:
                keep[item] = channel.overwrites[item]

            if (idx % rate == 0):
                await message.edit(
                    Messages.role_create_progress(
                        channel=channel.name,
                        perms=total_overwrites,
                        progress=utils.create_bar(idx + 1, total_overwrites),
                    )
                )

        # remove permission
        await channel.edit(sync_permissions=True)
        for item in channel.overwrites:
            await channel.set_permissions(item, overwrite=None)
        # add role
        await channel.set_permissions(role, read_messages=True)
        # restore special permissions
        for item in keep:
            await channel.set_permissions(item, overwrite=keep[item])

        await message.edit(
            Messages.role_create_done(
                role=role.name,
                perms=len(role.members)
            )
        )
        return role

    async def remove_perms(self, target, member: disnake.Member, guild):
        """Remove a target role / channel from a member."""
        roles, channels = self.get_target(target, guild)
        for role in roles:
            if role is not None and role in member.roles:
                await member.remove_roles(role)
        for channel in channels:
            if channel is None:
                continue

            perms = channel.permissions_for(member)
            if perms.administrator:
                continue  # User have administrator permission and it's useless do some operation.

            overwrite = channel.overwrites_for(member)
            # if overwrite.is_empty():
            #    continue  # Overwrite not found. User maybe have access from role.

            total_overwrites = len(channel.overwrites)
            if total_overwrites >= 490:
                await member.send(Messages.role_migration_allert(channel=channel))
                async with self.lock:
                    role = disnake.utils.get(guild.roles, name=channel.name)
                    if not role:
                        role = await self.create_role(channel, ignore=member)
            else:
                if overwrite != disnake.PermissionOverwrite(read_messages=True):
                    # Member have extra permissions and we don't want remove it.
                    # Instead of remove permission we set only read messages permission to deny.
                    overwrite.update(read_messages=False)
                    await channel.set_permissions(member, overwrite=overwrite)
                    continue

                await channel.set_permissions(member, overwrite=None)
                perms = channel.permissions_for(member)
                if perms.read_messages:
                    # The user still sees the channel. You need to create special permissions.
                    await channel.set_permissions(member, read_messages=False)

    def get_target(self, target, guild) -> Tuple[List[disnake.Role], List[disnake.abc.GuildChannel]]:
        """Detect if target is a channel a role or a group."""
        # Try a group first
        group = RoleGroupDB.get_group(target)
        if group is not None:
            roles, channels = [], []
            for role_id in group.role_ids:
                roles.append(disnake.utils.get(guild.roles, id=int(role_id)))
            for channel_id in group.channel_ids:
                channel = disnake.utils.get(guild.channels, id=int(channel_id))
                role = disnake.utils.get(guild.roles, name=channel.name)
                if role:
                    roles.append(role)
                else:
                    channels.append(channel)
            return roles, channels

        # if ID
        if isinstance(target, int) or target.isdigit():
            role = disnake.utils.get(guild.roles, id=int(target))
            channel = disnake.utils.get(guild.channels, id=int(target))
            if not role:
                role = disnake.utils.get(guild.roles, name=channel.name)
                channel = None if role else channel
        # else if name of role / #channel
        else:
            target = target[1:] if target[0] == "#" else target
            role = disnake.utils.get(guild.roles, name=target)
            channel = None if role else disnake.utils.get(guild.channels, name=target.lower())

        return [role], [channel]

    @commands.check(permission_check.mod_plus)
    @commands.slash_command(name="do_da_thing", description='hodi prdeli', guild_ids=[Base.config.guild_id])
    async def do_da_thing(self, inter: disnake.ApplicationCommandInteraction):
        guild = self.bot.get_guild(self.config.guild_id)
        logChan = self.bot.get_channel(self.config.log_channel)
        for channel in guild.channels:
            if channel.type == disnake.ChannelType.text:
                boolik = '-' in channel.name
                name = channel.name.split('-')[0] if boolik else channel.name
                sub = SubjectDetailsDB.get(name)
                if sub:
                    newName = sub.name + ', but ' + '-'.join(channel.name.split('-')[1:])
                    if channel.topic:
                        if channel.topic != sub.name and channel.topic != newName:
                            await logChan.send(channel.name+' - '+channel.topic+sub.name)
                    else:
                        await channel.edit(topic=sub.name if not boolik else newName)

    @commands.check(permission_check.mod_plus)
    @commands.slash_command(name="group", guild_ids=[Base.config.guild_id])
    async def group(self, inter):
        pass

    @group.sub_command(name="add", description=Messages.group_add)
    async def add_group(self, inter, name: str):
        group = RoleGroupDB.get_group(name)
        if group is not None:
            await inter.send(f"Groupa s názvem {name} už existuje.")
            return
        RoleGroupDB.add_group(name)
        await inter.send(f"Pridal jsem groupu {name}.")

    @group.sub_command(name="get", description=Messages.group_get)
    async def get_group(self, inter, name: str):
        group = RoleGroupDB.get_group(name)
        channels = ", ".join([f"<#{channel_id}>" for channel_id in group.channel_ids])
        await inter.send(f"Jmeno: {group.name}\n" f"Channel IDs: {channels}\n" f"Role IDs:{group.role_ids}")

    @group.sub_command(name="delete", description=Messages.group_delete)
    async def delete_group(self, inter, name: str):
        RoleGroupDB.group_delete(name)
        await inter.send(f"Odebral jsem groupu {name}")

    @group.sub_command(name="list", description=Messages.group_list)
    async def groups(self, inter):
        names = RoleGroupDB.group_names()
        groups = "\n".join(names)
        output = utils.cut_string_by_words(groups, 1900, "\n")
        await inter.send(f"```md\n# ACTIVE GROUPS:\n{output[0]}```")
        for message in output[1:]:
            await inter.channel.send(f"```md\n{message}```")

    @group.sub_command(name="add_channel_id", description=Messages.group_add_channel_id)
    async def add_channel_id(self, inter, name: str, channel_id: str):
        RoleGroupDB.group_add_channel_id(name, channel_id)
        await inter.send("Done")

    @group.sub_command(name="add_role_id", description=Messages.group_add_role_id)
    async def add_role_id(self, inter, name: str, role_id: str):
        RoleGroupDB.group_add_role_id(name, role_id)
        await inter.send("Done")

    @group.sub_command(name="reset_channels", description=Messages.group_reset_channels)
    async def group_reset_channels(self, inter, name: str):
        RoleGroupDB.group_reset_channels(name)
        await inter.send("Done")

    @group.sub_command(name="reset_roles", description=Messages.group_reset_roles)
    async def group_reset_roles(self, inter, name: str):
        RoleGroupDB.group_reset_roles(name)
        await inter.send("Done")

    @commands.check(permission_check.mod_plus)
    @commands.slash_command(name="channel", guild_ids=[Base.config.guild_id])
    async def channel(self, inter):
        pass

    @channel.sub_command(name="copy", description=Messages.role_channel_copy_brief)
    async def copy(self, inter, src: disnake.abc.GuildChannel,
                   dst: disnake.abc.GuildChannel):
        """
        Copy permissions from src channel to dst.
        Both channels are expected as tags or IDs
        """
        await inter.send(Messages.channel_copy_start)
        for key in src.overwrites:
            await dst.set_permissions(key, overwrite=src.overwrites[key])
        await inter.edit_original_response(Messages.channel_copy_done)

    @channel.sub_command(name="clone", description=Messages.role_channel_clone_brief)
    async def clone(self, inter, src: disnake.abc.GuildChannel, name: str):
        """Clone channel with same permissions as src."""
        await inter.send(Messages.channel_clone_start)
        new = await src.clone(name=name)
        await inter.edit_original_response(Messages.channel_clone_done(id=new.id))

    @channel.sub_command(name="create", description=Messages.role_channel_create_brief)
    async def create(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel_name,
        role: disnake.Role,
        rate: int = commands.Param(ge=1, default=10, description=Messages.channel_rate),
        category: disnake.CategoryChannel = None
    ):

        await inter.send(Messages.channel_create_start)
        guild = inter.guild
        overwrites = {guild.default_role: disnake.PermissionOverwrite(view_channel=False)}
        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        for index, member in enumerate(role.members):
            await channel.set_permissions(member, view_channel=True)
            if (index % rate == 0):
                await inter.edit_original_response(
                    f"• uživatelů: {len(role.members)}\n" + utils.create_bar(index+1, len(role.members))
                )

        await inter.edit_original_response(
            Messages.channel_create_done(
                channel=channel.mention,
                role=role.name,
                perms=len(role.members)
            )
        )

    @channel.sub_command(name="get_overwrites", description=Messages.channel_get_overwrites_brief)
    async def get_overwrites(
        self,
        inter: disnake.ApplicationCommandInteraction,
        rate: int = commands.Param(ge=1, default=10, description=Messages.channel_rate),
    ):
        """Get channels and count of user overwrites with view_channel=True."""
        await inter.send(Messages.channel_get_overwrites_start)
        total_overwrites = 0
        user_overwrites = 0
        channels_output = {}
        for index, channel in enumerate(inter.guild.channels):
            channel_user_overwrites = {
                member: permission for member, permission in channel.overwrites.items()
                if not isinstance(member, disnake.Role) and permission.view_channel
            }
            channel_overwrites = {
                role_or_member: permission for role_or_member, permission in channel.overwrites.items()
            }
            channels_output[channel] = f"user:{len(channel_user_overwrites)}, all: {len(channel_overwrites)}"
            if (index % rate == 0):
                await inter.edit_original_response(
                    f"• kanálů: {index+1}/{len(inter.guild.channels)}\n"
                    f"{utils.create_bar(index+1, len(inter.guild.channels))}"
                )
            user_overwrites += len(channel_user_overwrites)
            total_overwrites += len(channel_overwrites)

        output = []
        channels_output = dict(sorted(channels_output.items(), key=lambda item: item[1], reverse=True))
        with io.StringIO() as output:
            output.write(f"User overwrites total:{user_overwrites}\n")
            output.write(f"Total overwrites:{total_overwrites}\n\n")
            for channel, overwrites in channels_output.items():
                if isinstance(channel, disnake.CategoryChannel):
                    output.write(f"#{channel.name}(kategorie) - {overwrites}\n")
                else:
                    output.write(f"#{channel.name} - {overwrites}\n")
            output.seek(0)

            await inter.channel.send(file=disnake.File(output, filename="overwrites.txt"))
        await inter.edit_original_response(Messages.channel_get_overwrites_done)

    @channel.sub_command(
        name="overwrites_to_role",
        description=Messages.channel_overwrites_to_role_brief
    )
    async def overwrites_to_role(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel,
        rate: int = commands.Param(ge=1, default=10, description=Messages.channel_rate),
    ):
        """
        Create a new role with the same name as channel name.
        Give users with view_channel=True this role.
        Remove overwrites.
        """
        await inter.send(Messages.channel_overwrites_to_role_start)
        new_role = await inter.guild.create_role(name=channel.name)
        await channel.set_permissions(
            target=new_role,
            overwrite=disnake.PermissionOverwrite(view_channel=True)
        )
        channel_user_overwrites = {
            member: permission for member, permission in channel.overwrites.items()
            if not isinstance(member, disnake.Role) and permission.view_channel
        }
        for index, member in enumerate(channel_user_overwrites):
            await channel.set_permissions(member, overwrite=None)
            await member.add_roles(new_role)
            if (index % rate == 0):
                await inter.edit_original_response(
                    f"• overwrites: {index+1}/{len(channel_user_overwrites)}\n"
                    f"{utils.create_bar(index+1, len(channel_user_overwrites))}"
                )
        await inter.edit_original_response(Messages.channel_overwrites_to_role_done)

    @channel.sub_command(
        name="role_to_overwrites",
        description=Messages.channel_role_to_overwrites_brief
    )
    async def role_to_overwrites(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role,
        channel: disnake.TextChannel,
        rate: int = commands.Param(ge=1, default=10, description=Messages.channel_rate),
    ):
        """
        Create user overwrites from role for specific channel
        Give users view_channel=True who had this role.
        Remove role.
        """
        await inter.send(Messages.channel_role_to_overwrites_start)
        members = role.members
        await role.delete()

        for index, member in enumerate(members):
            await channel.set_permissions(member, view_channel=True)
            if (index % rate == 0):
                await inter.edit_original_response(
                    f"• overwrites: {index+1}/{len(members)}\n"
                    f"{utils.create_bar(index+1, len(members))}"
                )
        await inter.edit_original_response(Messages.channel_role_to_overwrites_done)

    @commands.check(permission_check.mod_plus)
    @commands.slash_command(name="remove_exclusive_roles", description=Messages.remove_exclusive_roles)
    async def remove_exclusive_roles(
        self,
        inter: disnake.ApplicationCommandInteraction,
        keep_role: disnake.Role,
        remove_role: disnake.Role = commands.Param(description=Messages.role_to_remove),
        rate: int = commands.Param(ge=1, default=10, description=Messages.channel_rate),
    ):
        """Find people who have both roles and remove their remove_role."""
        await inter.send(Messages.remove_exclusive_roles_start(role1=keep_role.name, role2=remove_role.name))
        role1_members = keep_role.members
        role2_members = remove_role.members

        members = set(role1_members).intersection(role2_members)

        if not members:
            await inter.send(Messages.role_no_exlusives)
            return

        for index, member in enumerate(members):
            await member.remove_roles(remove_role)
            if (index % rate == 0):
                await inter.edit_original_response(
                    f"• members: {index+1}/{len(members)}\n"
                    f"{utils.create_bar(index+1, len(members))}"
                )
        await inter.edit_original_response(Messages.remove_exclusive_roles_done)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id in self.config.role_channels:
            role_data = await self.get_join_role_data(message)
            await self.message_role_reactions(message, role_data)

    async def handle_reaction(self, ctx: ReactionContext):
        role_data = await self.get_join_role_data(ctx.message)
        for line in role_data:
            if str(ctx.emoji) == line[1]:
                await self.add_perms(line[0], ctx.member, ctx.guild)
                break
        else:
            await ctx.message.remove_reaction(ctx.emoji, ctx.member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        ctx: ReactionContext = await ReactionContext.from_payload(self.bot, payload)
        if ctx is None:
            return

        if ctx.channel.id in self.config.role_channels:
            role_data = await self.get_join_role_data(ctx.message)
            for line in role_data:
                if str(ctx.emoji) == line[1]:
                    await self.remove_perms(line[0], ctx.member, ctx.guild)
                    break


def setup(bot):
    bot.add_cog(Roles(bot))
