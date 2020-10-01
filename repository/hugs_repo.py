from typing import Optional, Tuple, Union

import discord

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.hugs import HugsTable

Member = Union[discord.Member, discord.User]


class HugsRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _get_member(member_id) -> Optional[HugsTable]:
        return session.query(HugsTable).filter(HugsTable.member_id == member_id).one_or_none()

    def get_members_stats(self, member_id) -> Tuple[int, int]:
        """
        :param member_id: Member's discord id
        :return: Tuple of [Given, Received] hugs, both zero if member not found
        """
        hugs = self._get_member(member_id)
        return (hugs.given, hugs.received) if hugs else (0, 0)

    @staticmethod
    def get_top_all_query():
        return session.query(HugsTable).order_by(HugsTable.given.desc(), HugsTable.received.desc())

    @staticmethod
    def get_top_givers_query(limit=10, offset=0):
        return session.query(HugsTable).order_by(HugsTable.given.desc())

    @staticmethod
    def get_top_receivers_query(limit=10, offset=0):
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
