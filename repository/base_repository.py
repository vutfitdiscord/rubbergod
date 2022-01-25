from config.app_config import config
from config import messages


class BaseRepository:
    def __init__(self):
        self.config = config
        self.messages = messages.Messages
