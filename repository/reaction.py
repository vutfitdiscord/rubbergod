from repository.base_repository import BaseRepository
import discord


class Reaction(BaseRepository):

    def __init__(self, client, utils, karma):
        super().__init__()
        self.client = client
        self.utils = utils
        self.karma = karma

    # Returns list of role names and emotes that represent them
    async def get_join_role_data(self, message):
        input_string = message.content
        input_string = input_string.replace(" - ", " ")
        input_string = input_string.replace(": ", " ")
        input_string = input_string.replace("**", "")
        output = []
        try:
            input_string = (input_string[input_string.index('\n')+1:]
                            .strip().split('\n'))
        except ValueError:
            await message.channel.send(self.messages.role_format
                                       .format(user=self.utils.generate_mention(
                                            message.author.id)))
            return output
        for line in input_string:
            line = line.split()
            if len(line) > 1:
                line = [line[0], line[1]]
                output.append(line)
            else:
                await message.channel.send(self.messages.role_invalid_line
                                           .format(user=self.utils.generate_mention(
                                                message.author.id), line=line[0]))
        return output

    # Adds reactions to message
    async def message_role_reactions(self, message, data):
        if message.channel.type is not discord.ChannelType.text:
            await message.channel.send(self.messages.role_not_on_server)
            guild = self.client.get_guild(self.config.guild_id)
        else:
            guild = message.guild
        for line in data:
            if (discord.utils.get(guild.roles,
                                  name=line[0]) is None):
                await message.channel.send(self.messages.role_not_role
                                           .format(user=self.utils.generate_mention(
                                               message.author.id), not_role=line[0]))
            else:
                try:
                    await message.add_reaction(line[1])
                except discord.errors.HTTPException:
                    await message.channel.send(
                            self.messages.role_invalid_line
                            .format(user=self.utils.generate_mention(
                                        message.author.id),
                                    not_emote=line[1], role=line[0]))

    async def add(self, payload):
        channel = self.client.get_channel(payload.channel_id)
        if channel is None:
            return
        if channel.type is discord.ChannelType.text:
            guild = channel.guild
        else:
            guild = self.client.get_guild(self.config.guild_id)
            if guild is None:
                raise Exception("Nemuzu najit guildu podle config.guild_id")
        member = guild.get_member(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        if member is None or message is None or member.bot:
            return

        if payload.emoji.is_custom_emoji():
            emoji = self.client.get_emoji(payload.emoji.id)
            if emoji is None:
                emoji = payload.emoji
        else:
            emoji = payload.emoji.name
        if message.content.startswith(self.config.role_string):
            role_data = await self.get_join_role_data(message)
            for line in role_data:
                if str(emoji) == line[1]:
                    await self.add_role_on_reaction(line[0], member,
                                                    message.channel,
                                                    guild)
                    break
            else:
                await message.remove_reaction(emoji, member)
        elif message.content.startswith(self.messages.karma_vote_message_hack):
            if emoji not in ["✅", "❌", "0⃣"]:
                await message.remove_reaction(emoji, member)
        elif member.id != message.author.id and\
                guild.id == self.config.guild_id and\
                message.channel.id not in self.config.karma_banned_channels and\
                self.config.karma_ban_role_id not in map(lambda x: x.id,
                                                         member.roles):
            if type(emoji) is str:
                self.karma.karma_emoji(message.author, member, emoji)
            else:
                self.karma.karma_emoji(message.author, member, emoji.id)

    async def remove(self, payload):
        channel = self.client.get_channel(payload.channel_id)
        if channel is None:
            return
        if channel.type is discord.ChannelType.text:
            guild = channel.guild
        else:
            guild = self.client.get_guild(self.config.guild_id)
            if guild is None:
                raise Exception("Nemuzu najit guildu podle config.guild_id")
        member = guild.get_member(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        if member is None or message is None or member.bot:
            return

        if payload.emoji.is_custom_emoji():
            emoji = self.client.get_emoji(payload.emoji.id)
            if emoji is None:
                emoji = payload.emoji
        else:
            emoji = payload.emoji.name
        if message.content.startswith(self.config.role_string):
            role_data = await self.get_join_role_data(message)
            for line in role_data:
                if str(emoji) == line[1]:
                    await self.remove_role_on_reaction(line[0], member,
                                                       message.channel,
                                                       guild)
                    break
        elif member.id != message.author.id and\
                guild.id == self.config.guild_id and\
                message.channel.id not in self.config.karma_banned_channels and\
                self.config.karma_ban_role_id not in map(lambda x: x.id,
                                                         member.roles):
            if type(emoji) is str:
                self.karma.karma_emoji_remove(message.author, member, emoji)
            else:
                self.karma.karma_emoji_remove(message.author, member, emoji.id)

    # Adds a role for user based on reaction
    async def add_role_on_reaction(self, role, member, channel, guild):
        role = discord.utils.get(guild.roles,
                                 name=role)
        max_role = discord.utils.get(guild.roles,
                                     name="Rubbergod")
        if role is not None:
            if role < max_role:
                await member.add_roles(role)
            else:
                await channel.send(self.messages.role_add_denied
                                   .format(user=self.utils.generate_mention(
                                           member.id), role=role.name))

    # Removes a role for user based on reaction
    async def remove_role_on_reaction(self, role, member, channel, guild):
        role = discord.utils.get(guild.roles,
                                 name=role)
        max_role = discord.utils.get(guild.roles,
                                     name="Rubbergod")
        if role is not None:
            if role in member.roles:
                if role < max_role:
                    await member.remove_roles(role)
                else:
                    await channel.send(self.messages.role_remove_denied
                                       .format(user=self.utils.generate_mention(
                                               member.id), role=role.name))
