from sqlalchemy import BIGINT, Column, DateTime, String

from repository.database import database


class StreamLink(database.base):
    __tablename__ = 'stream_links'

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    subject = Column(String, index=True, nullable=False)
    link = Column(String, nullable=False, index=True)
    member_name = Column(String, nullable=False)
    description = Column(String)
    thumbnail_url = Column(String)
    created_at = Column(DateTime, index=True)
