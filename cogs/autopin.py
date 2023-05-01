import datetime
from typing import List

import disnake
from disnake.ext import commands

import utils
from cogs.base import Base
from config.app_config import config
from config.messages import Messages
from permissions import permission_check
from repository import pin_repo
from repository.database.pin_map import PinMap


class AutoPin(Base, commands.Cog):
    def __init__(self, bot):
        self.warning_time = datetime.datetime.utcnow() - datetime.timedelta(
            minutes=config.autopin_warning_cooldown
        )
        self.bot = bot
        self.repo = pin_repo.PinRepository()

    @commands.check(permission_check.helper_plus)
    @commands.group(pass_context=True)
    async def pin(self, ctx: commands.Context):
        """
        Controls auto pin.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send(utils.get_command_group_signature(ctx))

    @pin.command(brief=Messages.autopin_add_brief)
    async def add(self, ctx: commands.Context, message_url: str):
        try:
            converter = commands.MessageConverter()
            message: disnake.Message = await converter.convert(ctx, message_url)

            if len(await message.channel.pins()) == 50:
                await ctx.send(Messages.autopin_max_pins_error)
                return

            self.repo.add_or_update_channel(str(message.channel.id), str(message.id))

            if not message.pinned:
                await message.pin()

            await ctx.send(Messages.autopin_add_done)
        except commands.errors.BadArgument:
            await ctx.send(Messages.autopin_add_unknown_message)
            return

    @pin.command(brief=Messages.autopin_remove_brief)
    async def remove(self, ctx: commands.Context, channel: disnake.TextChannel = None):
        if channel is None:
            channel = ctx.channel

        if self.repo.find_channel_by_id(str(channel.id)) is None:
            await ctx.send(utils.fill_message("autopin_remove_not_exists", channel_name=channel.name))
            return

        self.repo.remove_channel(str(channel.id))
        await ctx.send(Messages.autopin_remove_done)

    @pin.command(aliases=["list"], brief=Messages.autopin_list_brief)
    async def get_list(self, ctx: commands.Context):
        mappings: List[PinMap] = self.repo.get_mappings()

        if len(mappings) == 0:
            await ctx.send(Messages.autopin_no_messages)
            return

        lines: List[str] = []
        for item in mappings:

            try:
                channel: disnake.TextChannel = await self.bot.fetch_channel(int(item.channel_id))
            except disnake.errors.NotFound:
                lines.append(utils.fill_message("autopin_list_unknown_channel", channel_id=item.channel_id))
                self.repo.remove_channel(str(item.channel_id))
                continue

            try:
                message: disnake.Message = await channel.fetch_message(int(item.message_id))
                jump_url: str = message.jump_url
                msg: str = utils.fill_message("autopin_list_item", channel=channel.mention, url=jump_url)
            except disnake.errors.NotFound:
                msg: str = utils.fill_message("autopin_list_unknown_message", channel=channel.mention)
            finally:
                lines.append(msg)

        for part in utils.split_to_parts(lines, 10):
            await ctx.send("\n".join(part))

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel: disnake.TextChannel, last_pin):
        pin_map: PinMap = self.repo.find_channel_by_id(str(channel.id))

        if pin_map is None:
            # This channel is not used to check pins.
            return

        pins: List[disnake.Message] = await channel.pins()

        if not any(x.id == int(pin_map.message_id) for x in pins):
            # Mapped pin was removed. Remove from map.
            self.repo.remove_channel(str(channel.id))
            print(f"INFO:\tRemoved {channel.id} from PIN mapping. (on_guild_channel_pins_update)")
        elif pins[0].id != int(pin_map.message_id):
            message: disnake.Message = await channel.fetch_message(int(pin_map.message_id))

            if message is None:
                # Message not exists. Remove from map.
                self.repo.remove_channel(str(channel.id))
                return

            await message.unpin()
            await message.pin()
            print(f"INFO:\tMessage: {message.id} was repinned. (on_guild_channel_pins_update)")

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: disnake.RawMessageDeleteEvent):
        pin_map: PinMap = self.repo.find_channel_by_id(str(payload.channel_id))

        if pin_map is None or pin_map.message_id != str(payload.message_id):
            return

        self.repo.remove_channel(str(payload.channel_id))
        print(f"INFO:\tRemoved {pin_map.channel_id} from PIN mapping. (on_raw_message_delete)")

    async def handle_reaction(self, ctx):
        """
        if the message has X or more 'pin' emojis pin the message
        """
        message = ctx.message
        channel = ctx.channel
        if ctx.emoji == "📌" and ctx.member.id in config.autopin_banned_users:
            await message.remove_reaction("📌", ctx.member)
            return
        for reaction in message.reactions:
            if (
                reaction.emoji == "📌"
                and reaction.count >= config.autopin_count
                and not message.pinned
                and message.type == disnake.MessageType.default
                and message.channel.id not in config.autopin_banned_channels
            ):
                pin_count = await channel.pins()
                if len(pin_count) == 50:
                    now = datetime.datetime.utcnow()
                    if self.warning_time + datetime.timedelta(minutes=config.autopin_warning_cooldown) < now:
                        await channel.send(
                            f"{ctx.member.mention} {Messages.autopin_max_pins_error}\n{ctx.message.jump_url}"
                        )
                        self.warning_time = now
                    return
                users = await reaction.users().flatten()
                await self.log(message, users)
                await message.pin()
                await message.clear_reaction("📌")
                break

    async def log(self, message, users):
        """
        Logging message link and users that pinned message
        """
        embed = disnake.Embed(title="📌 Auto pin message log", color=0xEEE657)
        user_names = ", ".join([user.name for user in users])
        message_link = message.jump_url
        embed.add_field(name="Users", value=user_names if len(user_names) > 0 else "**Missing users**")
        embed.add_field(name="In channel", value=message.channel)
        embed.add_field(name="Message", value=message_link, inline=False)
        embed.timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        channel = self.bot.get_channel(config.log_channel)
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(AutoPin(bot))
