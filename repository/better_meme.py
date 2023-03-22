from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.better_meme import BetterMeme


class BetterMemeRepository(BaseRepository):

    def __init__(self):
        super().__init__()

    def get_member(self, user_id):
        return session.query(BetterMeme).filter(BetterMeme.member_ID == user_id).one_or_none()

    def add_post_to_repo(self, user_id, karma):
        member = self.get_karma_object(user_id)
        if member is not None:
            member.total_karma += karma
            member.posts += 1
        else:
            session.add(BetterMeme(member_ID=user_id, posts=1, total_karma=karma))

    def get_leaderboard(self, order_by, offset, limit=10):
        return session.query(BetterMeme).order_by(order_by).offset(offset).limit(limit)
