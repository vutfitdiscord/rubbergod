from config.app_config import Config
from config import messages


class BaseRepository:
    def __init__(self):
        self.config = Config
        self.messages = messages.Messages
