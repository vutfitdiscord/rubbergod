from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Date,
    PrimaryKeyConstraint,
    ForeignKey
)
from sqlalchemy.orm import relationship
from repository.database import database

class Review(database.base):
    __tablename__ = 'bot_review'

    id = Column(Integer, primary_key=True)
    member_ID = Column(String)
    anonym = Column(Boolean, default = True)
    subject = Column(String)
    tier = Column(Integer, default = 0)
    text_review = Column(String, default = None)
    date = Column(Date)
    relevance = relationship('ReviewRelevance')

class ReviewRelevance(database.base):
    __tablename__ = 'bot_review_relevance'
    __table_args__ = (
        PrimaryKeyConstraint('review', 'member_ID', name = 'key'),
    )

    member_ID = Column(String)
    vote = Column(Boolean, default = False)
    review = Column(Integer, ForeignKey('bot_review.id'))
