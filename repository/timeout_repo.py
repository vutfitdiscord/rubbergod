from datetime import datetime
from typing import List

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.timeout import Timeout


class TimeoutRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def get_timeout_users(self) -> List[Timeout]:
        return session.query(Timeout).all()

    def get_timeout_user(self, user_id: int):
        return session.query(Timeout).get(user_id)

    def add_timeout(self, user_id: int, end: datetime, reason: str):
        exists = self.get_timeout_user(user_id)
        if exists:
            exists.end = end
            exists.start = datetime.now()
            exists.reason = reason
            session.commit()
            return
        try:
            timeout = Timeout(user_id=user_id, start=datetime.now(), end=end, reason=reason)
            session.add(timeout)
            session.commit()
        except Exception:
            session.rollback()
            raise

    def remove_timeout(self, user_id: int):
        if self.get_timeout_user(user_id) is None:
            return
        try:
            session.query(Timeout).filter_by(user_id=user_id).delete()
            session.commit()
        except Exception:
            session.rollback()
            raise
