from repository.database import session
from repository.database.meme_repost import MemeRepost
from typing import Union

class MemeRepostRepo:
    @staticmethod
    def find_repost_by_id(message_id:int) -> Union[MemeRepost, None]:
        return session.query(MemeRepost).filter(MemeRepost.original_message_id == str(message_id)).one_or_none()

    @staticmethod
    def create_repost(original_message_id:int, repost_message_id:int, author_id:int, secondary_repost_message_id:int=None):
        item = MemeRepost(original_message_id=original_message_id, repost_message_id=repost_message_id, author_id=author_id, secondary_repost_message_id=secondary_repost_message_id)
        session.add(item)
        session.commit()