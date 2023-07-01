from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import BIGINT, Column, DateTime, String, desc, exists

from database import database, session


class StreamLinkDB(database.base):
    __tablename__ = 'stream_links'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    subject = Column(String, index=True, nullable=False)
    link = Column(String, nullable=False, index=True)
    member_name = Column(String, nullable=False)
    description = Column(String)
    thumbnail_url = Column(String)
    created_at = Column(DateTime, index=True)

    @classmethod
    def create(cls, subject: str, link: str, username: str, description: str,
               thumbnail_url: str, created_at: datetime) -> None:
        streamlink = StreamLinkDB(
            subject=subject,
            link=link,
            member_name=username,
            description=description,
            thumbnail_url=thumbnail_url,
            created_at=created_at
        )

        session.add(streamlink)
        session.commit()

    def remove(self) -> None:
        session.delete(self)
        session.commit()

    def merge(self) -> None:
        session.merge(self)
        session.commit()

    @classmethod
    def exists_link(cls, link: str) -> Optional[StreamLinkDB]:
        return session.query(exists().where(cls.link == link)).scalar()

    @classmethod
    def exists(cls, id: int) -> Optional[StreamLinkDB]:
        return session.query(exists().where(cls.id == id)).scalar()

    @classmethod
    def get_stream_by_id(cls, id: int) -> Optional[StreamLinkDB]:
        return session.query(cls).filter(cls.id == id).first()

    @classmethod
    def get_streamlinks_of_subject(cls, subject: str) -> List[StreamLinkDB]:
        return list(session.query(cls)
                    .filter(cls.subject == subject)
                    .order_by(desc("created_at"))
                    .all()
                    )

    @classmethod
    def get_subjects_with_stream(cls) -> List[StreamLinkDB]:
        return session.query(StreamLinkDB.subject).distinct().all()
