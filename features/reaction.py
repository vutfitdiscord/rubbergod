import discord
from discord.ext.commands import Bot

import utils
from config.config import Config
from config.messages import Messages
from features.base_feature import BaseFeature
from features.vote import Vote
from repository.karma_repo import KarmaRepository
from emoji import UNICODE_EMOJI


class Reaction(BaseFeature):

    def __init__(self, bot: Bot, karma_repository: KarmaRepository, voter: Vote):
        super().__init__(bot)
        self.karma_repo = karma_repository
        self.voter = voter

    def make_embed(self, page):
        embed = discord.Embed(title="Rubbergod",
                        description="Nejlepší a nejúžasnější bot ever.",
                        color=0xeee657)

        prefix = Config.default_prefix

        embed.add_field(name="Autor", value="Toaster#1111") 

        # Shows the number of servers the bot is member of.
        embed.add_field(name="Počet serverů s touto instancí bota",
                        value=f"{len(self.bot.guilds)}")

        embed.add_field(name="\u200b", value="Příkazy:", inline=False)

        info = Messages.info[page - 1]
            
        for command in info:
            embed.add_field(name=prefix + command[0],
                            value=command[1],
                            inline=False)

        embed.set_footer(text=f"Page {page} | Commit {utils.git_hash()}",
                        icon_url="https://cdn.discordapp.com/avatars/"
                                "560917571663298568/b93e8c1e93c2d18b"
                                "fbd226a0b614cf57.png?size=32")
        return embed

    # Returns list of role names and emotes that represent them
    async def get_join_role_data(self, message):
        input_string = message.content
        input_string = input_string.replace(" - ", " ")
        input_string = input_string.replace(": ", " ")
        input_string = input_string.replace("**", "")
        output = []
        try:
            input_string = (input_string[input_string.index('\n') + 1:]
                            .rstrip().split('\n'))
        except ValueError:
            await message.channel.send(
                Messages.role_format
                .format(user=utils.generate_mention(
                    message.author.id)
                )
            )
            return output
        for line in input_string:
            try:
                emoji = next(filter(lambda x: x[0] in UNICODE_EMOJI or x[0] == '<', line.split()))
                line = [line[:line.index(emoji) - 1], emoji]
                output.append(line)
            except:
                await message.channel.send(
                    Messages.role_invalid_line
                    .format(user=utils.generate_mention(
                        message.author.id),
                        line=line[0]
                    )
                )
        return output

    # Adds reactions to message
    async def message_role_reactions(self, message, data):
        if message.channel.type is not discord.ChannelType.text:
            await message.channel.send(Messages.role_not_on_server)
            guild = self.bot.get_guild(Config.guild_id)
        else:
            guild = message.guild
        for line in data:
            if (discord.utils.get(guild.roles,
                                  name=line[0]) is None):
                await message.channel.send(
                    Messages.role_not_role
                    .format(user=utils.generate_mention(
                        message.author.id),
                        not_role=line[0]))
            else:
                try:
                    await message.add_reaction(line[1])
                except discord.errors.HTTPException:
                    await message.channel.send(
                        Messages.role_invalid_line
                        .format(user=utils.generate_mention(
                            message.author.id),
                            not_emote=line[1], role=line[0]))

    async def add(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return
        if channel.type is discord.ChannelType.text:
            guild = channel.guild
        else:
            guild = self.bot.get_guild(Config.guild_id)
            if guild is None:
                raise Exception("Nemuzu najit guildu podle config.guild_id")
        member = guild.get_member(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        if member is None or message is None or member.bot:
            return

        if message.content[1:].startswith("vote") and message.content[0] in Config.command_prefix:
            await self.voter.handle_reaction(message)

        if payload.emoji.is_custom_emoji():
            emoji = self.bot.get_emoji(payload.emoji.id)
            if emoji is None:
                emoji = payload.emoji
        else:
            emoji = payload.emoji.name
        if message.content.startswith(Config.role_string):
            role_data = await self.get_join_role_data(message)
            for line in role_data:
                if str(emoji) == line[1]:
                    await self.add_role_on_reaction(line[0], member,
                                                    message.channel,
                                                    guild)
                    break
            else:
                await message.remove_reaction(emoji, member)
        elif message.content.startswith(Messages.karma_vote_message_hack):
            if emoji not in ["✅", "❌", "0⃣"]:
                await message.remove_reaction(emoji, member)
            else:
                users = []
                for reaction in message.reactions:
                    users.append(await reaction.users().flatten())
                # Flatten the final list
                users = [x for y in users for x in y]
                if users.count(member) > 1:
                    await message.remove_reaction(emoji, member)
        elif message.embeds and message.embeds[0].title == "Rubbergod":
            if emoji in ["◀", "▶"]:
                page = int(message.embeds[0].footer.text[5])
                info_len = len(Messages.info)
                if emoji == "▶":
                    next_page = page + 1
                    if next_page == info_len:
                        await message.remove_reaction("▶", self.bot.user)
                    if next_page == 2:
                        await message.add_reaction("◀")                            
                elif emoji == "◀":
                    next_page = page - 1
                    if next_page == 1:
                        await message.remove_reaction("◀", self.bot.user)
                    if next_page == info_len - 1:
                        await message.add_reaction("▶")
                if 1 <= next_page <= info_len:
                    embed = self.make_embed(next_page)
                    await message.edit(embed=embed)
            try:
                await message.remove_reaction(emoji, member)
            except:
                pass 
        elif member.id != message.author.id and\
                guild.id == Config.guild_id and\
                message.channel.id not in \
                Config.karma_banned_channels and \
                Config.karma_ban_role_id not in map(lambda x: x.id,
                                                    member.roles):
            if isinstance(emoji, str):
                self.karma_repo.karma_emoji(message.author, member, emoji)
            else:
                self.karma_repo.karma_emoji(message.author, member, emoji.id)

        # if the message has X or more 'pin' emojis pin the message
        if emoji == '📌':
            for reaction in message.reactions:
                if reaction.emoji == '📌' and \
                   reaction.count >= Config.pin_count:
                    try:
                        await message.pin()
                    except discord.HTTPException:
                        break

    async def remove(self, payload):
        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return
        if channel.type is discord.ChannelType.text:
            guild = channel.guild
        else:
            guild = self.bot.get_guild(Config.guild_id)
            if guild is None:
                raise Exception("Nemuzu najit guildu podle config.guild_id")
        member = guild.get_member(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        if member is None or message is None or member.bot:
            return

        if message.content[1:].startswith("vote") and message.content[0] in Config.command_prefix:
            await self.voter.handle_reaction(message)

        if payload.emoji.is_custom_emoji():
            emoji = self.bot.get_emoji(payload.emoji.id)
            if emoji is None:
                emoji = payload.emoji
        else:
            emoji = payload.emoji.name
        if message.content.startswith(Config.role_string):
            role_data = await self.get_join_role_data(message)
            for line in role_data:
                if str(emoji) == line[1]:
                    await self.remove_role_on_reaction(line[0], member,
                                                       message.channel,
                                                       guild)
                    break
        elif member.id != message.author.id and \
                guild.id == Config.guild_id and \
                message.channel.id not in \
                Config.karma_banned_channels and \
                Config.karma_ban_role_id not in map(lambda x: x.id,
                                                    member.roles):
            if isinstance(emoji, str):
                self.karma_repo.karma_emoji_remove(message.author,
                                                   member, emoji)
            else:
                self.karma_repo.karma_emoji_remove(
                    message.author, member, emoji.id)

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
                await channel.send(Messages.role_add_denied
                                   .format(user=utils.generate_mention(
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
                    await channel.send(
                        Messages.role_remove_denied
                        .format(user=utils.generate_mention(
                            member.id),
                            role=role.name
                        )
                    )
