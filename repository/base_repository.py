from config import config, messages


class BaseRepository:

    def __init__(self):
        self.config = config.Config
        self.messages = messages.Messages
