from datetime import datetime

from sqlalchemy import desc
from sqlalchemy.sql import exists

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.stream_link import StreamLink


class StreamLinksRepo(BaseRepository):
    def __init__(self):
        super().__init__()

    def create(self, subject: str, link: str, username: str, description: str,
               thumbnail_url: str, created_at: datetime):
        try:
            streamlink = StreamLink(
                subject=subject,
                link=link,
                member_name=username,
                description=description,
                thumbnail_url=thumbnail_url,
                created_at=created_at
            )

            session.add(streamlink)
            session.commit()
        except:  # noqa: E722
            session.rollback()
            raise

    def merge(self, streamlink: StreamLink):
        session.merge(streamlink)
        session.commit()

    def exists_link(self, link: str):
        return session.query(exists().where(StreamLink.link == link)).scalar()

    def exists(self, id: int):
        return session.query(exists().where(StreamLink.id == id)).scalar()

    def get_stream_by_id(self, id: int):
        return session.query(StreamLink).filter(StreamLink.id == id).first()

    def get_streamlinks_of_subject(self, subject: str):
        return list(session.query(StreamLink)
                    .filter(StreamLink.subject == subject)
                    .order_by(desc("created_at"))
                    .all()
                    )

    def remove(self, id: int):
        session.query(StreamLink).filter(StreamLink.id == id).delete()
        session.commit()

    def get_subjects_with_stream(self):
        return session.query(StreamLink.subject).distinct().all()
