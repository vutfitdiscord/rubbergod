from typing import List

from repository.database import session
from repository.database.exams import ExamsTermsMessage

class ExamsTermsMessageRepo:
    @staticmethod
    def create_term_message(message_id:int, channel_id:int) -> ExamsTermsMessage:
        item = ExamsTermsMessage(message_id=str(message_id), channel_id=str(channel_id))
        session.add(item)
        session.commit()
        return item

    @staticmethod
    def get_message_from_channel(channel_id:int) -> List[ExamsTermsMessage]:
        return session.query(ExamsTermsMessage).filter(ExamsTermsMessage.channel_id == str(channel_id)).all()

    @staticmethod
    def remove_term_message(message_id:int):
        session.query(ExamsTermsMessage).filter(ExamsTermsMessage.message_id == str(message_id)).delete()
        session.commit()

    @staticmethod
    def remove_from_channel(channel_id: int):
        session.query(ExamsTermsMessage).filter(ExamsTermsMessage.channel_id == str(channel_id)).delete()
        session.commit()
