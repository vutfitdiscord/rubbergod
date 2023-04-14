from sqlalchemy import func

import utils
from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.karma import Karma, Karma_emoji


class Karma_row_data():
    def __init__(self, value, position):
        self.value = value
        self.position = position


class Karma_data():
    def __init__(self, karma, positive, negative):
        self.karma = karma
        self.positive = positive
        self.negative = negative


class KarmaRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def get_ids_of_emojis_valued(self, val):
        """Returns a list of ids of emojis with specified value"""
        emojis = session.query(Karma_emoji).filter(Karma_emoji.value == val)
        return [emoji.emoji_ID for emoji in emojis]

    def get_all_emojis(self):
        """Returns a list of Karma_emoji objects."""
        return session.query(Karma_emoji)

    def emoji_value(self, emoji_id):
        """Returns the value of an emoji.
        If the emoji has not been voted for, returns 0."""
        val = self.emoji_value_raw(emoji_id)
        return val if val is not None else 0

    def emoji_value_raw(self, emoji_id):
        """Returns the value of an emoji.
        If the emoji has not been voted for, returns None."""
        emoji = session.query(Karma_emoji).\
            filter(Karma_emoji.emoji_ID == utils.str_emoji_id(emoji_id)).\
            one_or_none()
        return emoji.value if emoji else None

    def set_emoji_value(self, emoji_id, value: int):
        emoji = Karma_emoji(emoji_ID=utils.str_emoji_id(emoji_id), value=str(value))
        # Merge == 'insert on duplicate key update'
        session.merge(emoji)
        session.commit()

    def remove_emoji(self, emoji_id):
        session.query(Karma_emoji).\
            filter(Karma_emoji.emoji_ID == utils.str_emoji_id(emoji_id)).\
            delete()
        session.commit()

    def update_karma(self, member_id, giver_id, emoji_value, remove=False):
        member_getter = self.update_karma_get(member_id, emoji_value)
        member_giver = self.update_karma_give(giver_id, emoji_value, remove)

        session.commit()
        return [member_getter, member_giver]

    def update_karma_get(self, member_id, emoji_value):
        member_karma = self.get_karma_object(member_id)
        if member_karma is not None:
            member_karma.karma += emoji_value
        else:
            member_karma = Karma(member_ID=str(member_id), karma=emoji_value)
            session.add(member_karma)
        return member_karma

    def update_karma_give(self, giver_id, emoji_value, remove):
        if emoji_value > 0:
            if remove:
                column = 'negative'
            else:
                column = 'positive'
        else:
            if remove:
                column = 'positive'
            else:
                column = 'negative'

        if column == 'negative':
            emoji_value *= -1

        giver_karma = self.get_karma_object(giver_id)
        if giver_karma is not None:
            setattr(giver_karma, column, getattr(giver_karma, column) + emoji_value)
        else:
            # new giver
            giver_karma = Karma(member_ID=str(giver_id))
            setattr(giver_karma, column, emoji_value)
            session.add(giver_karma)
        return giver_karma

    def karma_emoji(self, member_id, giver_id, emoji_id):
        emoji_value = int(self.emoji_value(str(emoji_id)))
        if emoji_value:
            members_update = self.update_karma(member_id, giver_id, emoji_value)
            return members_update

    def karma_emoji_remove(self, member_id, giver_id, emoji_id):
        emoji_value = int(self.emoji_value(str(emoji_id)))
        if emoji_value:
            members_update = self.update_karma(member_id, giver_id, emoji_value * (-1), True)
            return members_update

    def get_karma_object(self, member_id):
        return session.query(Karma).\
            filter(Karma.member_ID == str(member_id)).one_or_none()

    def get_karma_position(self, column, karma):
        value = session.query(func.count(Karma.member_ID)).\
            filter(getattr(Karma, column) > karma).one()
        return value[0] + 1

    def get_karma(self, member_id):
        karma_object = self.get_karma_object(member_id)

        if karma_object is None:
            karma_object = Karma(karma=0, positive=0, negative=0)

        order = self.get_karma_position("karma", karma_object.karma)
        pos_order = self.get_karma_position("positive", karma_object.positive)
        neg_order = self.get_karma_position("negative", karma_object.negative)

        karma = Karma_row_data(karma_object.karma, order)
        positive = Karma_row_data(karma_object.positive, pos_order)
        negative = Karma_row_data(karma_object.negative, neg_order)

        result = Karma_data(karma, positive, negative)
        return result

    def leaderboard_query(self, atribute):
        return session.query(Karma).order_by(atribute)

    def get_leaderboard(self, atribute, offset=0, limit=10):
        leaderboard = session.query(Karma).order_by(atribute).offset(offset).limit(limit)
        return leaderboard

    def get_leaderboard_max(self):
        return session.query(Karma).count()

    def transfer_karma(self, from_user, to_user):
        from_user_karma = self.get_karma_object(from_user.id)
        to_user_karma = self.get_karma_object(to_user.id)

        # transfering from user that is not in the database
        if from_user_karma is None:
            return None

        # transfering to user that is not in the database
        if to_user_karma is None:
            to_user_karma = Karma(member_ID=str(to_user.id))
            session.add(to_user_karma)

        log_karma = Karma_data(from_user_karma.karma, from_user_karma.positive, from_user_karma.negative)

        # Move karma
        self.update_karma_get(to_user.id, from_user_karma.karma)
        self.update_karma_get(from_user.id, -from_user_karma.karma)

        # Move positive and negative reactions
        to_user_karma.positive += from_user_karma.positive
        to_user_karma.negative += from_user_karma.negative

        from_user_karma.positive = 0
        from_user_karma.negative = 0

        session.commit()
        return log_karma, [from_user_karma, to_user_karma]
