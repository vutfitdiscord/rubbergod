import datetime
import logging
import sys
import traceback
from functools import cached_property
from io import BytesIO
from pathlib import Path

import disnake
import requests
import sqlalchemy
from disnake.ext import commands
from PIL import Image, ImageDraw, ImageFont

import utils
from buttons.error import ErrorView
from cogs.gif.features import ImageHandler
from config.app_config import config
from config.messages import Messages
from database import session
from database.error import ErrorLogDB, ErrorRow
from database.stats import ErrorEvent
from permissions import custom_errors, permission_check
from rubbergod import Rubbergod

rubbegod_logger = logging.getLogger("rubbergod")


class ContextMock:
    """Create event context similar to commands.Context
    This will be used in ignore_errors function"""

    message: disnake.Message

    def __init__(self, bot: Rubbergod, arg):
        self.channel = getattr(arg, "channel", bot.get_channel(arg.channel_id))
        if hasattr(arg, "author"):
            self.author = arg.author
        elif hasattr(arg, "member"):
            self.author = arg.member
        else:
            self.author = bot.user

    async def send(self, *args, ephemeral=False):
        return await self.channel.send(*args)

    async def reply(self, *args, ephemeral=False):
        return await self.channel.send(*args)


class ErrorLogger:
    def __init__(self, bot: Rubbergod):
        self.bot = bot

    @cached_property
    def bot_dev_channel(self) -> disnake.TextChannel:
        return self.bot.get_channel(config.bot_dev_channel)

    @cached_property
    def log_channel(self) -> disnake.TextChannel:
        return self.bot.get_channel(config.log_channel)

    def set_image(self, embed: disnake.Embed, user: disnake.User, count: int):
        try:
            image_path = Path(__file__).parent.parent / "images/accident"
            background = Image.open(image_path / "xDaysBackground.png")
            head = Image.open(image_path / "xDaysHead.png")
            pliers = Image.open(image_path / "xDaysPliers.png")

            # add avatar
            url = user.display_avatar.replace(size=256, format="png")
            response = requests.get(url, timeout=10)
            avatar = Image.open(BytesIO(response.content))

            if not user.avatar:
                avatar = avatar.convert("RGB")

            avatar = ImageHandler.square_to_circle(avatar)
            avatar = avatar.resize((230, 230))
            avatar = avatar.crop((0, 0, 230, 200))
            background.paste(avatar, (560, 270), avatar)

            # set number
            font_size = 80 if count >= 10 else 90
            W, H = (150, 150)
            font = ImageFont.truetype(str(image_path / "OpenSans-Regular.ttf"), font_size)
            img_txt = Image.new("RGBA", (W, H), color=(255, 255, 255, 0))
            draw_txt = ImageDraw.Draw(img_txt)
            bbox = draw_txt.textbbox(xy=(0, 0), text=str(count), font=font)
            width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw_txt.text(((W - width) / 2, (H - height) / 2), str(count), font=font, fill="#000")
            img_txt = img_txt.rotate(10, expand=True, fillcolor=255)
            background.paste(img_txt, (1000, 130), img_txt)

            # add upper layers
            background.paste(head, (0, 0), head)
            background.paste(pliers, (0, 0), pliers)

            # add image to embed
            with BytesIO() as image_binary:
                background.save(image_binary, format="png")
                image_binary.seek(0)
                file = disnake.File(fp=image_binary, filename="accident.png")

            embed.set_image(file=file)
        except Exception as error:
            output = "".join(traceback.format_exception(type(error), error, error.__traceback__))
            rubbegod_logger.warning(output)

    def log_error_time(self, set=True) -> int:
        """Log details of last exception and return number of days since last exception"""
        try:
            today = datetime.date.today()
            last_exception = ErrorLogDB.get(ErrorRow.last_error)
            if last_exception:
                count = (today - last_exception.date).days
            else:
                count = 0
            if set:
                ErrorLogDB.set()
            return count
        except Exception:
            return 0

    def create_embed(
        self,
        command: str,
        args: str,
        author: disnake.User,
        guild: disnake.Guild,
        jump_url: str | None,
        extra_fields: dict[str, str] = None,
    ):
        count = self.log_error_time()
        embed = disnake.Embed(
            title=f"{count} days without an accident.\nIgnoring exception in {command}",
            color=0xFF0000,
        )
        if args:
            embed.add_field(name="Args", value=args)
        embed.add_field(name="Autor", value=author.mention)
        if guild and getattr(guild, "id", None) != config.guild_id:
            embed.add_field(name="Guild", value=getattr(guild, "name", guild))
        if jump_url:
            embed.add_field(name="Link", value=jump_url, inline=False)
        self.set_image(embed, author, count)
        if extra_fields:
            for name, value in extra_fields.items():
                embed.add_field(name=name, value=value)
        return embed

    def _get_app_cmd_prefix(self, command: commands.InvokableApplicationCommand):
        if isinstance(command, commands.InvokableUserCommand):
            return "User command - "
        elif isinstance(command, commands.InvokableMessageCommand):
            return "Message command - "
        elif isinstance(command, commands.InvokableSlashCommand) or isinstance(
            command, commands.slash_core.SubCommand
        ):
            return "/"
        else:
            # some new command probably? there aren't other options at the moment
            raise NotImplementedError

    async def _parse_context(self, ctx: disnake.ApplicationCommandInteraction | commands.Context):
        if isinstance(ctx, disnake.ApplicationCommandInteraction):
            args = " ".join(f"{key}={item}" for key, item in ctx.filled_options.items())
            prefix = self._get_app_cmd_prefix(ctx.application_command)
            return {
                "args": args,
                "cog": ctx.application_command.cog_name,
                "command": f"{prefix}{ctx.application_command.qualified_name}",
                "url": getattr(ctx.channel, "jump_url", "DM"),
            }
        elif isinstance(ctx, commands.Context):
            return {
                "args": ctx.message.content,
                "cog": ctx.cog.qualified_name,
                "command": f"?{ctx.command.qualified_name}",
                "url": getattr(ctx.message, "jump_url", "DM"),
            }
        else:
            raise NotImplementedError

    async def handle_error(
        self,
        ctx: disnake.ApplicationCommandInteraction | commands.Context,
        error: Exception,
    ):
        if await self.ignore_errors(ctx, error):
            # error was handled
            return
        parsed_ctx = await self._parse_context(ctx)
        embed = self.create_embed(
            parsed_ctx["command"], parsed_ctx["args"][:1000], ctx.author, ctx.guild, parsed_ctx["url"]
        )
        error_log = ErrorEvent.log(
            event_name=parsed_ctx["command"],
            cog=parsed_ctx["cog"],
            datetime=datetime.datetime.now(),
            user_id=str(ctx.author.id),
            args=parsed_ctx["args"],
            exception=type(error).__name__,
            traceback="\n".join(traceback.format_exception(type(error), error, error.__traceback__)),
        )
        utils.embed.add_author_footer(embed, author=ctx.author, additional_text=[f"ID: {error_log.id}"])

        # send context of command with personal information to logging channel
        if parsed_ctx["command"] == "/diplom":
            await self.log_channel.send(embed=embed, view=ErrorView())
            embed.remove_field(0)  # remove args from embed for sending to bot dev channel

        # send context of verify command with personal information to logging channel only
        if parsed_ctx["command"] == "/verify":
            await self.log_channel.send(embed=embed, view=ErrorView())
            return

        await self.bot_dev_channel.send(embed=embed, view=ErrorView())

    async def handle_event_error(self, event: str, args):
        """Handle error in events"""
        # there is usually just one arg
        arg = args[0]
        error = sys.exc_info()[1]
        if error is None:
            return  # Not sure how this could happen
        author = getattr(arg, "author", self.bot.user)
        if await self.ignore_errors(ContextMock(self.bot, arg), error):
            # error was handled
            return
        if event == "on_message":
            message_id = arg.id
            if hasattr(arg, "guild") and arg.guild:
                event_guild = arg.guild.name
                url = f"https://discord.com/channels/{arg.guild.id}/{arg.channel.id}/{message_id}"
            else:
                event_guild = url = "DM"
            embeds = [
                self.create_embed(
                    command="on_message",
                    args=arg.content,
                    author=author,
                    guild=event_guild,
                    jump_url=url,
                )
            ]
        elif event in ["on_raw_reaction_add", "on_raw_reaction_remove"]:
            embeds = await self.handle_reaction_error(arg)
        else:
            embeds = [
                self.create_embed(
                    command=event,
                    args=args,
                    author=author,
                    guild=arg.guild,
                    jump_url=None,
                )
            ]
        error_log = ErrorEvent.log(
            event_name=event,
            cog="System",  # log all events under system cog as it is hard to find actual cog
            datetime=datetime.datetime.now(),
            user_id=author.id if author else "rubbergod",
            args=str(args),
            exception=type(error).__name__,
            traceback="\n".join(
                traceback.format_exception(type(error) if error else None, error, error.__traceback__)
            ),
        )
        utils.embed.add_author_footer(embeds[-1], author=author, additional_text=[f"ID: {error_log.id}"])
        await self.bot_dev_channel.send(embeds=embeds, view=ErrorView())

    async def handle_reaction_error(self, arg: disnake.RawReactionActionEvent):
        """Handle error in on_raw_reaction_add/remove events"""
        embeds = []

        message_id = getattr(arg, "message_id", None)
        channel_id = getattr(arg, "channel_id", None)
        user_id = getattr(arg, "user_id", None)
        if hasattr(arg, "guild_id"):
            guild = self.bot.get_guild(arg.guild_id)
            event_guild = guild.name
            if channel_id:
                channel = guild.get_channel(channel_id)
                if message_id and channel:
                    message = await channel.fetch_message(message_id)
                    if message is not None:
                        message = message.content[:1000]
            else:
                event_guild = "DM"
                message = message_id
        if user_id:
            user = self.bot.get_user(arg.user_id)
        if not user:
            user = arg.user_id
        else:
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel and message_id:
                    message = await channel.fetch_message(message_id)
                    if message:
                        if message.content:
                            message = message.content[:1000]
                        elif message.embeds:
                            embeds.extend(message.embeds)
                            message = "Embed v předchozí zprávě"
                        elif message.attachments:
                            message_out = ""
                            for attachment in message.attachments:
                                message_out += f"{attachment.url}\n"
                            message = message_out
                else:
                    message = message_id
        extra_fields = {"Reaction": getattr(arg, "emoji", "None")}
        url = (
            event_guild
            if event_guild == "DM"
            else f"https://discord.com/channels/{guild.id}/{channel_id}/{message_id}"
        )
        embeds.append(
            self.create_embed(
                command=arg.event_type,
                args=message,
                author=user,
                guild=event_guild,
                jump_url=url,
                extra_fields=extra_fields,
            )
        )
        return embeds

    def create_error_embed(
        self, inter: disnake.ApplicationCommandInteraction, prefix: str, filled_options=None
    ):
        filled_options = filled_options or inter.filled_options
        embed = self.create_embed(
            f"{prefix}{inter.application_command.qualified_name}",
            filled_options,
            inter.author,
            inter.guild,
            f"https://discord.com/channels/{inter.guild_id}/{inter.channel_id}/{inter.id}",
        )
        return embed

    async def ignore_errors(
        self,
        ctx: disnake.ApplicationCommandInteraction | commands.Context | ContextMock,
        error: BaseException,
    ) -> bool:
        """Handle general errors that can be ignored or responded to user
        Returns whether error was handled or not"""

        # in following code 'ctx' is used for shared errors between text and slash commands
        # if 'inter' is used then the error is specific for slash commands
        # both classes have similar function so we are not differentiating them here

        # SHARED ERRORS
        if isinstance(error, disnake.errors.DiscordServerError):
            return True

        if isinstance(error, (sqlalchemy.exc.InternalError, sqlalchemy.exc.PendingRollbackError)):
            # rollback transaction that caused the error but continue with the log
            session.rollback()
            return False

        if isinstance(error, commands.CommandNotFound):
            slash_comms = [command.name for command in self.bot.slash_commands]
            invoked = ctx.message.content.split(" ")[0][1:]
            if invoked in slash_comms:
                command_id = utils.general.get_command_id(self.bot, invoked)
                await ctx.reply(Messages.moved_command(name=invoked, id=command_id))
            return True

        if (
            isinstance(error, permission_check.NotHelperPlusError)
            or isinstance(error, permission_check.NotSubmodPlusError)
            or isinstance(error, permission_check.NotModPlusError)
            or isinstance(error, permission_check.NotAdminError)
        ):
            await ctx.send(error.message)
            return True

        if isinstance(error, commands.UserNotFound):
            await ctx.send(Messages.user_not_found(user=ctx.author.mention))
            return True

        if isinstance(error, commands.MemberNotFound):
            await ctx.send(Messages.member_not_found(member=ctx.author.mention))
            return True

        if isinstance(error, custom_errors.ApiError):
            await ctx.send(error.message)
            return True

        # LEGACY COMMANDS
        if isinstance(ctx, commands.Context):
            if (
                isinstance(error, commands.BadArgument)
                or isinstance(error, commands.MissingAnyRole)
                or isinstance(error, commands.MissingRequiredArgument)
            ) and hasattr(ctx.command, "on_error"):
                return True

            if isinstance(error, commands.UserInputError):
                await ctx.send(Messages.user_input_error)
                return True

        # SLASH COMMANDS / INTERACTIONS
        inter = ctx
        if hasattr(error, "original"):
            if isinstance(error.original, disnake.errors.InteractionTimedOut):
                embed = self.create_error_embed(inter, "/", "Interaction timed out")
                await self.bot_dev_channel.send(embed=embed)
                return True

            if isinstance(error.original, disnake.errors.Forbidden):
                # bot can't send messages to user
                if error.original.code == 50007:
                    await inter.channel.send(Messages.blocked_bot(user=inter.author.id))
                    return True
        else:
            if isinstance(error, disnake.errors.Forbidden):
                if error.code == 50007:
                    await ctx.send(Messages.blocked_bot(user=inter.author.id))
                    return True

        if isinstance(error, custom_errors.InvalidTime):
            await inter.send(error.message, ephemeral=True)
            return True

        if isinstance(error, commands.MessageNotFound):
            await inter.send(Messages.message_not_found, ephemeral=True)
            return True

        if isinstance(error, commands.CommandInvokeError):
            await inter.send(Messages.command_invoke_error)
            # return False, because we want to log these errors
            return False

        if isinstance(error, commands.CommandOnCooldown):
            time = datetime.datetime.now() + datetime.timedelta(seconds=error.retry_after)
            retry_after = disnake.utils.format_dt(time, style="R")
            await ctx.send(Messages.spamming(user=ctx.author.id, time=retry_after), ephemeral=True)
            return True

        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send(Messages.guild_only)
            return True

        # CheckFailure must be last in the list of errors, because it is the most generic one.
        if isinstance(error, commands.CheckFailure):
            await ctx.send(Messages.missing_perms(user=ctx.author.id))
            return True

        return False
