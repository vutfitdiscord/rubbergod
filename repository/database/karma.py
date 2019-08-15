from sqlalchemy import Column, String, Integer
from repository.database import database, session


class Karma(database.base):
    __tablename__ = 'bot_karma'

    member_ID = Column(String, primary_key=True)
    karma = Column(Integer)
    positive = Column(Integer)
    negative = Column(Integer)


def main():
    database.base.metadata.create_all(database.db)

    foo = Karma(member_ID="123", karma=15, positive=12, negative=54)
    bar = Karma(member_ID="43", karma=24, positive=68, negative=5)
    session.add(foo)
    session.add(bar)
    session.commit()

    data = session.query(Karma)
    for row in data:
        print(row)
