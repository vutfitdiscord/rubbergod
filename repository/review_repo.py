import datetime

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.review import Review


class ReviewRepository(BaseRepository):

    def __init__(self):
        super().__init__()
    
    def get_subject_reviews(self, subject):
        return session.query(Review).filter(Review.subject == subject)
    
    def get_all_reviews(self):
        return session.query(Review)

    def get_review_by_author_subject(self, author_id, subject):
        return session.query(Review).filter(
            Review.subject == subject,
            Review.member_ID == str(author_id)
        ).first()

    def update_review(self, id, tier, anonym: bool, text):
        review = Review(
            id = id,
            tier = tier,
            anonym = anonym,
            text_review = text,
            date = datetime.date.today()
        )
        session.merge(review)
        session.commit()

    def add_review(self, author, subject, tier, anonym: bool, text):
        review = Review(
            member_ID = str(author),
            subject = subject,
            tier = tier,
            anonym = anonym,
            text_review = text,
            date = datetime.date.today()
        )
        session.add(review)
        session.commit()
