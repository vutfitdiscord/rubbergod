from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Column, Integer, String

from database import database, session


class SubscriptionDB(database.base):  # type: ignore
    __tablename__ = "subscription"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    forum_id = Column(String)
    tag = Column(String)

    @classmethod
    def add(cls, user_id: str | int, forum_id: str | int, tag: str) -> None:
        sub = cls(
            user_id=str(user_id),
            forum_id=str(forum_id),
            tag=tag,
        )
        session.add(sub)
        session.commit()

    @classmethod
    def get(cls, user_id: str | int, forum_id: str | int, tag: str) -> Optional[SubscriptionDB]:
        return (
            session.query(cls)
            .filter((cls.user_id == str(user_id)) & (cls.forum_id == str(forum_id)) & (cls.tag == tag))
            .one_or_none()
        )

    @classmethod
    def get_tags(cls, user_id: str | int, forum_id: str | int) -> List[SubscriptionDB]:
        tags = (
            session.query(cls.tag)
            .filter((cls.user_id == str(user_id)) & (cls.forum_id == str(forum_id)))
            .all()
        )
        # from list of sets to list of strings
        return [tag[0] for tag in tags]

    @classmethod
    def get_user(cls, user_id: str | int) -> List[SubscriptionDB]:
        return session.query(cls).filter(cls.user_id == str(user_id)).all()

    @classmethod
    def get_channel(cls, forum_id: str | int) -> List[SubscriptionDB]:
        return session.query(cls).filter(cls.forum_id == str(forum_id)).all()

    def remove(self) -> None:
        session.delete(self)
        session.commit()


class AlreadyNotifiedDB(database.base):  # type: ignore
    __tablename__ = "subscription_notified"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String)
    thread_id = Column(String)

    @classmethod
    def get(cls, thread_id: str | int) -> List[str]:
        users = session.query(cls.user_id).filter(cls.thread_id == str(thread_id)).all()
        # from list of sets to list of strings
        return [user[0] for user in users]

    @classmethod
    def add(cls, user_id: str | int, thread_id: str | int) -> None:
        new = cls(user_id=str(user_id), thread_id=str(thread_id))
        session.add(new)
        session.commit()
