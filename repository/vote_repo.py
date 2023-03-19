from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.vote import Vote


class VoteRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def get_pending_votes(self) -> List[Vote]:
        return session.query(Vote).filter(or_(Vote.ends_at is None, Vote.ends_at >= datetime.now()))

    def add_vote(
        self, message_id: int, channel_id: int, ends_at: Optional[datetime], is_one_of: bool = False
    ):
        vote = Vote(message_id=message_id, channel_id=channel_id, ends_at=ends_at, is_one_of=is_one_of)
        session.add(vote)
        session.commit()

    def finish_vote(self, message_id: str):
        session.query(Vote).filter(Vote.message_id == message_id).delete()
        session.commit()
