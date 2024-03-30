"""
Cog implementing channels and roles management. Copying/creating channels with permissions.
"""

import io

import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
from database.review import SubjectDetailsDB
from permissions import permission_check

from .messages_cz import MessagesCZ


class Roles(Base, commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.check(permission_check.mod_plus)
    @commands.slash_command(
        name="add_channels_description",
        description=MessagesCZ.channel_add_description_brief,
        guild_ids=[Base.config.guild_id],
    )
    async def add_channels_description(
        self,
        inter: disnake.ApplicationCommandInteraction,
        rate: int = commands.Param(ge=1, default=10, description=MessagesCZ.channel_rate_param),
    ):
        await inter.send(MessagesCZ.channel_add_topic_start)
        message = await inter.original_message()
        for index, channel in enumerate(inter.guild.channels):
            if channel.type != disnake.ChannelType.text:
                continue

            if index % rate == 0:
                progress_bar = utils.create_bar(index + 1, len(inter.guild.channels))
                await message.edit(
                    MessagesCZ.channel_add_topic_progress(
                        index=index + 1,
                        total=len(inter.guild.channels),
                        progress_bar=progress_bar,
                        channel=channel.mention,
                    )
                )

            is_private = "-" in channel.name
            name = channel.name.split("-")[0] if is_private else channel.name
            subject_name = SubjectDetailsDB.get(name)
            if not subject_name:
                continue

            private_name = f"{subject_name}, but " + "-".join(channel.name.split("-")[1:])
            if channel.topic:
                if channel.topic != subject_name and channel.topic != private_name:
                    await self.log_channel.send(
                        MessagesCZ.channel_different_topic(channel=channel, topic=subject_name)
                    )
            else:
                await channel.edit(topic=subject_name if not is_private else private_name)
        await message.edit(MessagesCZ.channel_add_topic_done)

    @commands.check(permission_check.mod_plus)
    @commands.slash_command(name="channel", guild_ids=[Base.config.guild_id])
    async def channel(self, inter: disnake.ApplicationCommandInteraction):
        pass

    @channel.sub_command(name="copy", description=MessagesCZ.role_channel_copy_brief)
    async def copy(
        self,
        inter: disnake.ApplicationCommandInteraction,
        src: disnake.abc.GuildChannel,
        dst: disnake.abc.GuildChannel,
    ):
        """
        Copy permissions from src channel to dst.
        Both channels are expected as tags or IDs
        """
        await inter.send(MessagesCZ.channel_copy_start)
        for key in src.overwrites:
            await dst.set_permissions(key, overwrite=src.overwrites[key])
        await inter.edit_original_response(MessagesCZ.channel_copy_done)

    @channel.sub_command(name="clone", description=MessagesCZ.role_channel_clone_brief)
    async def clone(
        self, inter: disnake.ApplicationCommandInteraction, src: disnake.abc.GuildChannel, name: str
    ):
        """Clone channel with same permissions as src."""
        await inter.send(MessagesCZ.channel_clone_start)
        new = await src.clone(name=name)
        await inter.edit_original_response(MessagesCZ.channel_clone_done(id=new.id))

    @channel.sub_command(name="create", description=MessagesCZ.role_channel_create_brief)
    async def create(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel_name: str,
        role: disnake.Role,
        rate: int = commands.Param(ge=1, default=10, description=MessagesCZ.channel_rate_param),
        category: disnake.CategoryChannel = None,
    ):
        await inter.send(MessagesCZ.channel_create_start)
        guild = inter.guild
        overwrites = {guild.default_role: disnake.PermissionOverwrite(view_channel=False)}
        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        for index, member in enumerate(role.members):
            await channel.set_permissions(member, view_channel=True)
            if index % rate == 0:
                await inter.edit_original_response(
                    f"• uživatelů: {len(role.members)}\n" + utils.create_bar(index + 1, len(role.members))
                )

        await inter.edit_original_response(
            MessagesCZ.channel_create_done(channel=channel.mention, role=role.name, perms=len(role.members))
        )

    @channel.sub_command(name="get_overwrites", description=MessagesCZ.channel_get_overwrites_brief)
    async def get_overwrites(
        self,
        inter: disnake.ApplicationCommandInteraction,
        rate: int = commands.Param(ge=1, default=10, description=MessagesCZ.channel_rate_param),
    ):
        """Get channels and count of user overwrites with view_channel=True."""
        await inter.send(MessagesCZ.channel_get_overwrites_start)
        total_overwrites = 0
        user_overwrites = 0
        channels_output = {}
        for index, channel in enumerate(inter.guild.channels):
            channel_user_overwrites = {
                member: permission
                for member, permission in channel.overwrites.items()
                if not isinstance(member, disnake.Role) and permission.view_channel
            }
            channel_overwrites = {
                role_or_member: permission for role_or_member, permission in channel.overwrites.items()
            }
            channels_output[channel] = f"user:{len(channel_user_overwrites)}, all: {len(channel_overwrites)}"
            if index % rate == 0:
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
        await inter.edit_original_response(MessagesCZ.channel_get_overwrites_done)

    @channel.sub_command(name="overwrites_to_role", description=MessagesCZ.channel_overwrites_to_role_brief)
    async def overwrites_to_role(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: disnake.TextChannel,
        rate: int = commands.Param(ge=1, default=10, description=MessagesCZ.channel_rate_param),
    ):
        """
        Create a new role with the same name as channel name.
        Give users with view_channel=True this role.
        Remove overwrites.
        """
        await inter.send(MessagesCZ.channel_overwrites_to_role_start)
        new_role = await inter.guild.create_role(name=channel.name)
        await channel.set_permissions(
            target=new_role, overwrite=disnake.PermissionOverwrite(view_channel=True)
        )
        channel_user_overwrites = {
            member: permission
            for member, permission in channel.overwrites.items()
            if not isinstance(member, disnake.Role) and permission.view_channel
        }
        for index, member in enumerate(channel_user_overwrites):
            await channel.set_permissions(member, overwrite=None)
            await member.add_roles(new_role)
            if index % rate == 0:
                await inter.edit_original_response(
                    f"• overwrites: {index+1}/{len(channel_user_overwrites)}\n"
                    f"{utils.create_bar(index+1, len(channel_user_overwrites))}"
                )
        await inter.edit_original_response(MessagesCZ.channel_overwrites_to_role_done)

    @channel.sub_command(name="role_to_overwrites", description=MessagesCZ.channel_role_to_overwrites_brief)
    async def role_to_overwrites(
        self,
        inter: disnake.ApplicationCommandInteraction,
        role: disnake.Role,
        channel: disnake.TextChannel,
        rate: int = commands.Param(ge=1, default=10, description=MessagesCZ.channel_rate_param),
    ):
        """
        Create user overwrites from role for specific channel
        Give users view_channel=True who had this role.
        Remove role.
        """
        await inter.send(MessagesCZ.channel_role_to_overwrites_start)
        members = role.members
        await role.delete()

        for index, member in enumerate(members):
            await channel.set_permissions(member, view_channel=True)
            if index % rate == 0:
                await inter.edit_original_response(
                    f"• overwrites: {index+1}/{len(members)}\n" f"{utils.create_bar(index+1, len(members))}"
                )
        await inter.edit_original_response(MessagesCZ.channel_role_to_overwrites_done)

    @commands.check(permission_check.mod_plus)
    @commands.slash_command(name="remove_exclusive_roles", description=MessagesCZ.remove_exclusive_roles)
    async def remove_exclusive_roles(
        self,
        inter: disnake.ApplicationCommandInteraction,
        keep_role: disnake.Role,
        remove_role: disnake.Role = commands.Param(description=MessagesCZ.role_to_remove_param),
        rate: int = commands.Param(ge=1, default=10, description=MessagesCZ.channel_rate_param),
    ):
        """Find people who have both roles and remove their remove_role."""
        await inter.send(
            MessagesCZ.remove_exclusive_roles_start(role1=keep_role.name, role2=remove_role.name)
        )
        role1_members = keep_role.members
        role2_members = remove_role.members

        members = set(role1_members).intersection(role2_members)

        if not members:
            await inter.send(MessagesCZ.role_no_exlusives)
            return

        for index, member in enumerate(members):
            await member.remove_roles(remove_role)
            if index % rate == 0:
                await inter.edit_original_response(
                    f"• members: {index+1}/{len(members)}\n" f"{utils.create_bar(index+1, len(members))}"
                )
        await inter.edit_original_response(MessagesCZ.remove_exclusive_roles_done)
