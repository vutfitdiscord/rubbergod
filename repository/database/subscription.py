from sqlalchemy import BigInteger, Column, Integer
from repository.database import database


class Subscription(database.base):
    __tablename__ = "bot_channel_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger)
    channel_id = Column(BigInteger)

    def __repr__(self):
        return (
            f'<Subscription id="{self.id}" '
            f'user_id="{self.user_id}" channel_id="{self.channel_id}">'
        )
