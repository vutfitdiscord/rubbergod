import argparse
import logging

import disnake
from disnake import AllowedMentions, Intents, TextChannel
from disnake.ext import commands

import database.db_migrations as migrations
from buttons.error import ErrorView
from cogs.contestvote.views import View as ContestVoteView
from cogs.report.views import ReportAnonymView, ReportAnswerOnlyView, ReportGeneralView, ReportMessageView
from config.app_config import config
from config.messages import Messages
from features.error import ErrorLogger
from features.logger import setup_logging
from features.presence import Presence

setup_logging()
rubbergod_logger = logging.getLogger("rubbergod")

parser = argparse.ArgumentParser()
parser.add_argument("--init_db", action="store_true", help="Creates missing DB tables without start bot.")
args = parser.parse_args()

if args.init_db:
    migrations.init_db()
    exit(0)

is_initialized = False

intents = Intents.none()
intents.guilds = True
intents.members = True
intents.emojis = True
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.presences = True
intents.moderation = True
intents.automod_execution = True


class Rubbergod(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(*config.command_prefix),
            help_command=None,
            case_insensitive=True,
            allowed_mentions=AllowedMentions(roles=False, everyone=False, users=True),
            intents=intents,
            command_sync_flags=commands.CommandSyncFlags(sync_commands_debug=False),
        )
        # Create missing tables at start
        migrations.init_db()

        # Features
        self.presence = Presence(self)
        self.err_logger = ErrorLogger(self)

        self.init_cogs()

    async def on_ready(self) -> None:
        """If RubberGod is ready"""
        # Inspired from https://github.com/sinus-x/rubbergoddess/blob/master/rubbergoddess.py
        global is_initialized
        if is_initialized:
            return
        is_initialized = True

        self.init_views()
        bot_room: TextChannel = self.get_channel(config.bot_room)
        if bot_room is not None:
            await bot_room.send(Messages.on_ready_message)

        await self.application_info()
        await self.presence.set_presence()
        rubbergod_logger.info("Ready")

    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id in [Messages.trash_delete_id, "bookmark:delete"]:
            try:
                await inter.message.delete()
            except disnake.NotFound:
                pass

    async def on_error(self, event, *args, **kwargs):
        return await self.err_logger.handle_event_error(event, args)

    def init_cogs(self) -> None:
        self.load_extension("cogs.system")
        rubbergod_logger.info("SYSTEM loaded")

        for extension in config.extensions:
            self.load_extension(f"cogs.{extension}")
            rubbergod_logger.info(f"{extension.upper()} loaded")

    def init_views(self) -> None:
        """Instantiate views for persistent interactions with bot"""
        self.add_view(ReportAnonymView(self))
        self.add_view(ReportAnswerOnlyView(self))
        self.add_view(ReportGeneralView(self))
        self.add_view(ReportMessageView(self))
        self.add_view(ContestVoteView(self))
        self.add_view(ErrorView())


rubbergod = Rubbergod()

rubbergod.run(config.key)
