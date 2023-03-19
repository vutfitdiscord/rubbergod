from sqlalchemy import Column, String

from repository.database import database


class PinMap(database.base):
    __tablename__ = 'bot_pin_map'

    channel_id = Column(String, primary_key=True)
    message_id = Column(String)
