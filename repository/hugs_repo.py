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
    def _get_member(member_id):
        return session.query(HugsTable).filter(HugsTable.member_id == member_id).one_or_none()

    @staticmethod
    def get_members_stats(member_id: int) -> Optional[Tuple[int, int]]:
        """
        :param member_id: Member's discord id
        :return: Tuple of [Given, Received] hugs, both zero if member not found
        """
        hugs = (
            session.query(HugsTable.given, HugsTable.received)
            .filter(HugsTable.member_id == member_id)
            .one_or_none()
        )
        return hugs if hugs else 0, 0

    @staticmethod
    def _get_hugs(limit, offset, order_by: tuple = None, columns=None):
        # TODO
        return session.query(HugsTable).order_by(*order_by).limit(limit).offset(offset).all()

    def get_top_all(self, limit=10, offset=0):
        return self._get_hugs(limit, offset, order_by=(HugsTable.given.desc(), HugsTable.received.desc()))

    def get_top_givers(self, limit=10, offset=0):
        return self._get_hugs(
            limit, offset, order_by=HugsTable.given.desc(), columns=(HugsTable.member_id, HugsTable.given)
        ).all()

    def get_top_receivers(self, limit=10, offset=0):
        return self._get_hugs(
            limit,
            offset,
            order_by=HugsTable.received.desc(),
            columns=(HugsTable.member_id, HugsTable.received),
        ).all()

    def do_hug(self, giver_id: int, receiver_id: int):
        giver = self._get_member(giver_id)
        if not giver:
            giver = HugsTable(member_id=giver_id, given=0)
        giver.given += 1

        receiver = self._get_member(receiver_id)
        if not receiver:
            receiver = HugsTable(member_id=receiver_id, received=0)
        receiver.received += 1

        session.add_all((giver, receiver))
        session.commit()
