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

    def get_timeout_users_filter_self(self, isself: bool = False) -> List[Timeout]:
        return session.query(Timeout).filter(Timeout.isself == isself).all()

    def get_timeout_user(self, user_id: int):
        return session.query(Timeout).get(user_id)

    def add_timeout(
        self,
        user_id: int,
        mod_id: int,
        start: datetime,
        end: datetime,
        reason: str,
        isself: bool = False
    ):
        """
        Add the user and their timeout/selftimeout to the database.
        Save all datetimes in the database without timezone information.
        """
        exists = self.get_timeout_user(user_id)
        if exists:
            exists.mod_id = mod_id
            exists.start = start
            exists.end = end
            exists.length = end - start
            exists.reason = reason
            exists.isself = isself
            session.commit()
            return
        try:
            timeout = Timeout(
                user_id=user_id,
                mod_id=mod_id,
                start=start,
                end=end,
                length=end-start,
                reason=reason,
                isself=isself
            )
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
