from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Column, Integer, String, func
from sqlalchemy.orm import Query
from sqlalchemy.sql.operators import ColumnOperators

import utils
from database import database, session


class KarmaRowData():
    def __init__(self, value: int, position: int):
        self.value: int = value
        self.position: int = position


class KarmaData():
    def __init__(self, karma: KarmaRowData, positive: KarmaRowData, negative: KarmaRowData):
        self.karma: KarmaRowData = karma
        self.positive: KarmaRowData = positive
        self.negative: KarmaRowData = negative


class KarmaDB(database.base):
    __tablename__ = 'bot_karma'

    member_ID = Column(String, primary_key=True)
    karma = Column(Integer, default=0)
    positive = Column(Integer, default=0)
    negative = Column(Integer, default=0)

    @classmethod
    def get_karma_object(cls, member_id: str) -> Optional[KarmaDB]:
        return session.query(cls).filter(cls.member_ID == str(member_id)).one_or_none()

    @classmethod
    def update_karma(
        cls, member_id: str, giver_id: str, emoji_value: int, remove: bool = False
    ) -> List[KarmaDB]:
        member_getter = cls.update_karma_get(member_id, emoji_value)
        member_giver = cls.update_karma_give(giver_id, emoji_value, remove)

        session.commit()
        return [member_getter, member_giver]

    @classmethod
    def update_karma_get(cls, member_id: str, emoji_value: int) -> KarmaDB:
        member_karma = cls.get_karma_object(member_id)
        if member_karma is not None:
            member_karma.karma += emoji_value
        else:
            member_karma = cls(member_ID=str(member_id), karma=emoji_value)
            session.add(member_karma)
        return member_karma

    @classmethod
    def update_karma_give(cls, giver_id: str, emoji_value: int, remove: bool) -> KarmaDB:
        if emoji_value > 0:
            column = 'negative' if remove else 'positive'
        else:
            column = 'positive' if remove else 'negative'

        if column == 'negative':
            emoji_value *= -1

        giver_karma = cls.get_karma_object(giver_id)
        if giver_karma is not None:
            setattr(giver_karma, column, getattr(giver_karma, column) + emoji_value)
        else:
            # new giver
            giver_karma = cls(member_ID=str(giver_id))
            setattr(giver_karma, column, emoji_value)
            session.add(giver_karma)
        return giver_karma

    @classmethod
    def karma_emoji(cls, member_id: str, giver_id: str, emoji_id: str) -> Optional[List[KarmaDB]]:
        emoji_value = KarmaEmojiDB.emoji_value(str(emoji_id))
        if emoji_value:
            members_update = cls.update_karma(member_id, giver_id, emoji_value)
            return members_update

    @classmethod
    def karma_emoji_remove(cls, member_id: str, giver_id: str, emoji_id: str) -> Optional[List[KarmaDB]]:
        emoji_value = KarmaEmojiDB.emoji_value(str(emoji_id))
        if emoji_value:
            members_update = cls.update_karma(member_id, giver_id, emoji_value * (-1), True)
            return members_update

    @classmethod
    def get_karma_position(cls, column: str, karma: int) -> int:
        value = session.query(func.count(cls.member_ID)).filter(getattr(cls, column) > karma).one()
        return value[0] + 1

    @classmethod
    def get_karma(cls, member_id: str) -> KarmaData:
        karma_object = cls.get_karma_object(member_id)

        if karma_object is None:
            karma_object = cls(karma=0, positive=0, negative=0)

        order = cls.get_karma_position("karma", karma_object.karma)
        pos_order = cls.get_karma_position("positive", karma_object.positive)
        neg_order = cls.get_karma_position("negative", karma_object.negative)

        karma = KarmaRowData(karma_object.karma, order)
        positive = KarmaRowData(karma_object.positive, pos_order)
        negative = KarmaRowData(karma_object.negative, neg_order)

        result = KarmaData(karma, positive, negative)
        return result

    @classmethod
    def leaderboard_query(cls, atribute: ColumnOperators) -> Query:
        return session.query(cls).order_by(atribute)

    @classmethod
    def transfer_karma(cls, from_user: str, to_user: str) -> KarmaData:
        from_user_karma = cls.get_karma_object(from_user)
        to_user_karma = cls.get_karma_object(to_user)

        # transfering from user that is not in the database
        if from_user_karma is None:
            return None

        # transfering to user that is not in the database
        if to_user_karma is None:
            to_user_karma = cls(member_ID=to_user)
            session.add(to_user_karma)

        log_karma = KarmaData(from_user_karma.karma, from_user_karma.positive, from_user_karma.negative)

        # Move karma
        cls.update_karma_get(to_user, from_user_karma.karma)
        cls.update_karma_get(from_user, -from_user_karma.karma)

        # Move positive and negative reactions
        to_user_karma.positive += from_user_karma.positive
        to_user_karma.negative += from_user_karma.negative

        from_user_karma.positive = 0
        from_user_karma.negative = 0

        session.commit()
        return log_karma


class KarmaEmojiDB(database.base):
    __tablename__ = 'bot_karma_emoji'
    emoji_ID = Column(String, primary_key=True)
    value = Column(Integer, default=0)

    @classmethod
    def get_ids_of_emojis_valued(cls, val: int) -> List[str]:
        """Returns a list of emoji ids with specified value"""
        emojis: List[cls] = session.query(cls).filter(cls.value == val)
        return [emoji.emoji_ID for emoji in emojis]

    @classmethod
    def get_all_emojis(cls) -> List[KarmaEmojiDB]:
        """Returns to list of KarmaEmojiDB objects."""
        return session.query(cls).all()

    @classmethod
    def emoji_value(cls, emoji_id: str) -> int:
        """Returns the value of an emoji.
        If the emoji has not been voted for, returns 0."""
        val = cls.emoji_value_raw(emoji_id)
        return val if val is not None else 0

    @classmethod
    def emoji_value_raw(cls, emoji_id: str) -> Optional[int]:
        """Returns the value of an emoji.
        If the emoji has not been voted for, returns None."""
        emoji = session.query(cls).filter(cls.emoji_ID == utils.str_emoji_id(emoji_id)).one_or_none()
        return emoji.value if emoji else None

    @classmethod
    def set_emoji_value(cls, emoji_id: str, value: int) -> None:
        emoji = cls(emoji_ID=utils.str_emoji_id(emoji_id), value=str(value))
        session.merge(emoji)
        session.commit()

    @classmethod
    def remove_emoji(cls, emoji_id: str) -> None:
        session.query(cls).filter(cls.emoji_ID == utils.str_emoji_id(emoji_id)).delete()
        session.commit()
