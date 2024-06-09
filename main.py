import argparse

import database.db_migrations as migrations
from config.app_config import config
from features.error import ErrorLogger
from features.logger import setup_logging
from features.presence import Presence
from rubbergod import Rubbergod

setup_logging()

parser = argparse.ArgumentParser()
parser.add_argument("--init_db", action="store_true", help="Creates missing DB tables without start bot.")
args = parser.parse_args()

if args.init_db:
    migrations.init_db()
    exit(0)


class Bot(Rubbergod):
    def __init__(self):
        super().__init__()
        # Features
        self.presence = Presence(self)
        self.err_logger = ErrorLogger(self)

        self.init_cogs()


rubbergod = Bot()

rubbergod.run(config.key)
