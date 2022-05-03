from sqlalchemy import Column, String
from repository.database import database


class ExamsTermsMessage(database.base):
    __tablename__ = "exams_terms_message"

    message_id = Column(String, primary_key=True)
    channel_id = Column(String, nullable=False, index=True, unique=True) # One message per channel
