from sqlalchemy import Column, String, Boolean
from repository.database import database


class PinMap(database.base):
    __tablename__ = 'bot_pin_map'

    channel_id = Column(String, primary_key=True)
    message_id = Column(String)
    is_active = Column(Boolean, default=False)
