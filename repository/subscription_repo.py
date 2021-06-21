from typing import List, Optional

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.subscription import Subscription


class SubscriptionRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def add_subscription(self, user_id: int, channel_id: int) -> Optional[Subscription]:
        if self.get_subscription(user_id, channel_id) is not None:
            subscription = None
        else:
            subscription = Subscription(user_id=user_id, channel_id=channel_id)
            session.add(subscription)
            session.commit()
        return subscription

    def get_subscription(self, user_id: int, channel_id: int) -> Optional[Subscription]:
        query = (
            session.query(Subscription)
            .filter_by(
                user_id=user_id,
                channel_id=channel_id,
            )
            .one_or_none()
        )
        return query

    def remove_subscription(self, user_id: int, channel_id: int) -> int:
        count = (
            session.query(Subscription)
            .filter_by(
                user_id=user_id,
                channel_id=channel_id,
            )
            .delete()
        )
        session.commit()
        return count

    def get_channel_subscribers(self, channel_id: int) -> List[Subscription]:
        query = session.query(Subscription).filter_by(channel_id=channel_id).all()
        return query

    def get_user_subscriptions(self, user_id: int) -> List[Subscription]:
        query = session.query(Subscription).filter_by(user_id=user_id).all()
        return query

    def get_all(self) -> List[Subscription]:
        query = session.query(Subscription).all()
        return query
