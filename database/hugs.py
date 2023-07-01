from __future__ import annotations

from collections import namedtuple
from typing import Optional, Tuple, Union

import disnake
from sqlalchemy import BIGINT, Column, Integer
from sqlalchemy.orm import Query

from database import database, session

Member = Union[disnake.Member, disnake.User]
UserHugStats = namedtuple("UserHugStats", ("given", "received"))


class HugsTableDB(database.base):
    __tablename__ = "bot_hugs"

    member_id = Column(BIGINT, primary_key=True, nullable=False, unique=True, autoincrement=False)

    # indexes make ~3s difference on table with 2.5k rows,
    # when polling for 'order by <received> [desc]' (leaderboards etc.)
    given = Column(Integer, default=0, nullable=False, index=True)
    received = Column(Integer, default=0, nullable=False, index=True)

    def get_members_stats(self, member_id: int) -> UserHugStats:
        """
        :param member_id: Member's discord id
        :return: Tuple of [Given, Received] hugs, both zero if member not found
        """
        hugs = self._get_member(int(member_id))
        return UserHugStats(hugs.given, hugs.received) if hugs else UserHugStats(0, 0)

    def get_member_position(self, member_stats: UserHugStats) -> Tuple[int, int]:
        if member_stats.given > 0:
            give_position = 1 + session.query(HugsTableDB).filter(
                HugsTableDB.given > member_stats.given).count()
        else:
            # zero means you are last
            give_position = self._get_count(order_by=HugsTableDB.given)

        if member_stats.received > 0:
            recv_position = 1 + session.query(HugsTableDB).filter(
                HugsTableDB.received > member_stats.received).count()
        else:
            recv_position = self._get_count(order_by=HugsTableDB.received)

        return give_position, recv_position

    def do_hug(self, giver_id: int = None, receiver_id: int = None) -> None:
        if giver_id:
            giver = self._get_member(giver_id)
            if not giver:
                giver = HugsTableDB(member_id=giver_id, given=0)

            giver.given += 1
            session.add(giver)

        if receiver_id:
            receiver = self._get_member(receiver_id)
            if not receiver:
                receiver = HugsTableDB(member_id=receiver_id, received=0)

            receiver.received += 1
            session.add(receiver)

        if giver_id is not None or receiver_id is not None:
            session.commit()

    @classmethod
    def _get_member(cls, member_id: int) -> Optional[HugsTableDB]:
        return session.query(cls).filter(cls.member_id == int(member_id)).one_or_none()

    @classmethod
    def _get_count(cls, order_by: Column = None) -> int:
        return session.query(cls).order_by(order_by).count()

    @classmethod
    def get_top_all_query(cls) -> Query:
        return session.query(cls).order_by(cls.given.desc(), cls.received.desc())

    @classmethod
    def get_top_givers_query(cls) -> Query:
        return session.query(cls).order_by(cls.given.desc())

    @classmethod
    def get_top_receivers_query(cls) -> Query:
        return session.query(cls).order_by(cls.received.desc())
