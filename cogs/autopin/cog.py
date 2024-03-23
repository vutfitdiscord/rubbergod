"""
Cog controlling auto pinning of messages. Create priority pinned messages in channels.
"""

import datetime

import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
from config import cooldowns
from database.pin_map import PinMapDB
from permissions import permission_check, room_check

from .features import PIN_CHANNEL_TYPE, AutopinFeatures
from .messages_cz import MessagesCZ


class AutoPin(Base, commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.warning_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            minutes=self.config.autopin_warning_cooldown
        )
        self.bot = bot
        self.check = room_check.RoomCheck(bot)
        self.pin_features = AutopinFeatures(bot)

    async def api(self, message: commands.Context, params: list):
        """Sending pins from channel to grillbot"""
        if "command" in params and params["command"] is not None:
            if params["command"] == "pin_get_all":
                channel = self.bot.get_channel(int(params["channel"]))
                if channel is None:
                    return 1, "Channel not found"
                pins = await channel.pins()
                if not pins:
                    return 0, MessagesCZ.no_pins
                if params["type"] == "markdown":
                    res = await self.pin_features.create_markdown_file(channel, pins)
                    return 0, res
                else:
                    res = await self.pin_features.create_json_file(channel, pins)
                    return 0, res
        return 1, "Command not found"

    @commands.check(permission_check.helper_plus)
    @commands.slash_command(name="pin_mod")
    async def pin_mod(self, inter: disnake.GuildCommandInteraction):
        await inter.response.defer()

    @pin_mod.sub_command(name="add", description=MessagesCZ.add_brief)
    async def add(self, inter: disnake.ApplicationCommandInteraction, message_url: str):
        try:
            converter = commands.MessageConverter()
            message: disnake.Message = await converter.convert(inter, message_url)

            if message.is_system():
                await inter.send(MessagesCZ.system_message)
                return

            if len(await message.channel.pins()) == 50:
                await inter.send(MessagesCZ.max_pins_error)
                return

            PinMapDB.add_or_update_channel(str(message.channel.id), str(message.id))

            if not message.pinned:
                await message.pin()

            await inter.send(MessagesCZ.add_done)
        except commands.MessageNotFound:
            await inter.send(MessagesCZ.add_unknown_message)
            return

    @pin_mod.sub_command(name="remove", description=MessagesCZ.remove_brief)
    async def remove(self, inter: disnake.ApplicationCommandInteraction, channel: disnake.TextChannel = None):
        if channel is None:
            channel = inter.channel

        if PinMapDB.find_channel_by_id(str(channel.id)) is None:
            await inter.send(MessagesCZ.remove_not_exists(channel_name=channel.mention))
            return

        PinMapDB.remove_channel(str(channel.id))
        await inter.send(MessagesCZ.remove_done)

    @pin_mod.sub_command(name="list", description=MessagesCZ.list_brief)
    async def get_list(self, inter: disnake.ApplicationCommandInteraction):
        mappings: list[PinMapDB] = PinMapDB.get_mappings()

        if not mappings:
            await inter.send(MessagesCZ.no_messages)
            return

        lines: list[str] = []
        for item in mappings:
            try:
                channel = await utils.get_or_fetch_channel(self.bot, int(item.channel_id))
            except disnake.NotFound:
                lines.append(MessagesCZ.list_unknown_channel(channel_id=item.channel_id))
                PinMapDB.remove_channel(str(item.channel_id))
                continue

            try:
                message: disnake.Message = await channel.fetch_message(int(item.message_id))
                msg: str = MessagesCZ.list_item(channel=channel.mention, url=message.jump_url)
            except disnake.NotFound:
                msg: str = MessagesCZ.list_unknown_message(channel=channel.mention)
            finally:
                lines.append(msg)

        await inter.send(MessagesCZ.list_info)
        for part in utils.split_to_parts(lines, 10):
            await inter.channel.send("\n".join(part))

    @cooldowns.long_cooldown
    @commands.slash_command(name="pin")
    async def pin(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.defer(ephemeral=True)

    @pin.sub_command(name="get_all", description=MessagesCZ.get_all_brief)
    async def get_all(
        self,
        inter: disnake.ApplicationCommandInteraction,
        channel: PIN_CHANNEL_TYPE = None,
        type: str = commands.Param(
            description="Typ výstupu. Markdown/JSON", choices=["json", "markdown"], default="markdown"
        ),
    ):
        """Get all pins from channel and send it to user in markdown file"""
        channel = inter.channel if channel is None else channel
        pins = await channel.pins()
        if not pins:
            await inter.send(MessagesCZ.no_pins)
            return

        if type == "markdown":
            file = await self.pin_features.create_markdown_file(channel, pins)
        else:
            file = await self.pin_features.create_json_file(channel, pins)

        channel_mention = channel.mention if hasattr(channel, "mention") else "**DM s botem**"
        await inter.send(file=file)
        await inter.edit_original_response(MessagesCZ.get_all_done(channel_name=channel_mention))

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel: disnake.TextChannel, _):
        """
        repin priority pin if new pin is added
        """
        pin_map: PinMapDB = PinMapDB.find_channel_by_id(str(channel.id))

        # This channel is not used to check priority pins.
        if pin_map is None:
            return

        pins: list[int] = [message.id for message in await channel.pins()]

        # Mapped pin was removed. Remove from map.
        if int(pin_map.message_id) not in pins:
            PinMapDB.remove_channel(str(channel.id))

        # check priority pin is first
        elif pins[0] != int(pin_map.message_id):
            message: disnake.Message = await channel.fetch_message(int(pin_map.message_id))

            # Message doesn't exist. Remove from map.
            if message is None:
                PinMapDB.remove_channel(str(channel.id))
                return

            await message.unpin()
            await message.pin()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: disnake.RawMessageDeleteEvent):
        """
        if the priority pin is deleted remove it from the map
        """
        pin_map: PinMapDB = PinMapDB.find_channel_by_id(str(payload.channel_id))

        if pin_map is None or pin_map.message_id != str(payload.message_id):
            return

        PinMapDB.remove_channel(str(payload.channel_id))

    async def handle_reaction(self, ctx: commands.Context):
        """
        if the message has X or more 'pushpin' emojis pin the message
        """
        message = ctx.message
        channel = ctx.channel
        if ctx.emoji == "📌" and ctx.member.id in self.config.autopin_banned_users:
            await message.remove_reaction("📌", ctx.member)
            return
        for reaction in message.reactions:
            if (
                reaction.emoji == "📌"
                and reaction.count >= self.config.autopin_count
                and not message.pinned
                and not message.is_system()
                and message.channel.id not in self.config.autopin_banned_channels
            ):
                # prevent spamming max_pins_error message in channel
                pin_count = await channel.pins()
                if len(pin_count) == 50:
                    now = datetime.datetime.now(datetime.timezone.utc)
                    cooldown = datetime.timedelta(minutes=self.config.autopin_warning_cooldown)
                    if self.warning_time + cooldown < now:
                        await channel.send(
                            f"{ctx.member.mention} {MessagesCZ.max_pins_error}\n{ctx.message.jump_url}"
                        )
                        self.warning_time = now
                    return

                users = await reaction.users().flatten()
                await self.pin_features.log(message, users)
                await message.pin()
                await message.clear_reaction("📌")
                break
