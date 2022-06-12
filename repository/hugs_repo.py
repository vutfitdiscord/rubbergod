from collections import namedtuple
from typing import Optional, Tuple, Union

import disnake

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.hugs import HugsTable

Member = Union[disnake.Member, disnake.User]

UserHugStats = namedtuple("UserHugStats", ("given", "received"))


class HugsRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _get_member(member_id) -> Optional[HugsTable]:
        return session.query(HugsTable).filter(HugsTable.member_id == member_id).one_or_none()

    def get_members_stats(self, member_id) -> UserHugStats:
        """
        :param member_id: Member's discord id
        :return: Tuple of [Given, Received] hugs, both zero if member not found
        """
        hugs = self._get_member(member_id)
        return UserHugStats(hugs.given, hugs.received) if hugs else UserHugStats(0, 0)

    @staticmethod
    def _get_count(order_by=None):
        # this should be cached for some time
        return session.query(HugsTable).order_by(order_by).count()

    def get_member_position(self, member_stats: UserHugStats) -> Tuple[int, int]:
        if member_stats.given > 0:
            give_position = 1 + session.query(HugsTable).filter(HugsTable.given > member_stats.given).count()
        else:
            # zero means you are last
            give_position = self._get_count(order_by=HugsTable.given)

        if member_stats.received > 0:
            recv_position = 1 + session.query(HugsTable).filter(
                HugsTable.received > member_stats.received).count()
        else:
            recv_position = self._get_count(order_by=HugsTable.received)

        return give_position, recv_position

    @staticmethod
    def get_top_all_query():
        return session.query(HugsTable).order_by(HugsTable.given.desc(), HugsTable.received.desc())

    @staticmethod
    def get_top_givers_query():
        return session.query(HugsTable).order_by(HugsTable.given.desc())

    @staticmethod
    def get_top_receivers_query():
        return session.query(HugsTable).order_by(HugsTable.received.desc())

    def do_hug(self, giver_id: int = None, receiver_id: int = None):
        if giver_id:
            giver = self._get_member(giver_id)
            if not giver:
                giver = HugsTable(member_id=giver_id, given=0)

            giver.given += 1
            session.add(giver)

        if receiver_id:
            receiver = self._get_member(receiver_id)
            if not receiver:
                receiver = HugsTable(member_id=receiver_id, received=0)

            receiver.received += 1
            session.add(receiver)

        if giver_id is not None or receiver_id is not None:
            session.commit()
