import datetime
from sqlalchemy import func, desc

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.review import Review, ReviewRelevance, Subject


class ReviewRepository(BaseRepository):

    def __init__(self):
        super().__init__()

    def get_subject_reviews(self, subject):
        return session.query(
            Review,
            func.count(Review.relevance)
            .filter(ReviewRelevance.vote)
            .label('total')).filter(Review.subject == subject)\
            .outerjoin(Review.relevance).group_by(Review)\
            .order_by(desc('total'))

    def get_all_reviews(self):
        return session.query(Review)

    def get_review_by_author_subject(self, author_id, subject):
        return session.query(Review).filter(
            Review.subject == subject,
            Review.member_ID == str(author_id)
        ).first()

    def update_review(self, id, tier, anonym: bool, text):
        review = Review(
            id=id,
            tier=tier,
            anonym=anonym,
            text_review=text,
            date=datetime.date.today()
        )
        session.merge(review)
        session.commit()

    def add_review(self, author, subject, tier, anonym: bool, text):
        try:
            review = Review(
                member_ID=str(author),
                subject=subject,
                tier=tier,
                anonym=anonym,
                text_review=text,
                date=datetime.date.today()
            )
            session.add(review)
            session.commit()
        except Exception:
            session.rollback()
            raise

    def remove(self, id):
        session.query(Review).filter(Review.id == id).delete()

    def get_votes_count(self, review_id, vote: bool):
        return session.query(ReviewRelevance).filter(
            ReviewRelevance.review == review_id,
            ReviewRelevance.vote == vote
        ).count()

    def get_vote_by_author(self, review_id, author):
        return session.query(ReviewRelevance).filter(
            ReviewRelevance.review == review_id,
            ReviewRelevance.member_ID == author
        ).first()

    def add_vote(self, review_id, vote: bool, author):
        relevance = ReviewRelevance(
            member_ID=author,
            vote=vote,
            review=review_id
        )
        session.merge(relevance)
        session.commit()

    def remove_vote(self, review_id, author):
        session.query(ReviewRelevance).filter(
            ReviewRelevance.review == review_id,
            ReviewRelevance.member_ID == author
        ).delete()

    def get_subject(self, shortcut):
        return session.query(Subject).filter(Subject.shortcut == shortcut)

    def add_subject(self, shortcut):
        subject = Subject(
            shortcut=shortcut
        )
        session.merge(subject)
        session.commit()
