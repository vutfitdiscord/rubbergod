from sqlalchemy import Column, String

from database import database


class User_backup(database.base):
    __tablename__ = 'bot_user_backup'

    member_ID = Column(String, primary_key=True)
