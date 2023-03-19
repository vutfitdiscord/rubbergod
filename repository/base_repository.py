from config import messages
from config.app_config import config


class BaseRepository:
    def __init__(self):
        self.config = config
        self.messages = messages.Messages
