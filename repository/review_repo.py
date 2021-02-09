import datetime
import math
from sqlalchemy import func, desc, asc

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.review import Review, ReviewRelevance, Subject, Subject_details


class ReviewRepository(BaseRepository):
    def __init__(self):
        super().__init__()

    def get_subject_reviews(self, subject):
        return (
            session.query(
                Review,
                func.avg(Review.tier).label("avg_tier"),
                func.count(Review.relevance).filter(ReviewRelevance.vote).label("total"),
            )
            .filter(Review.subject == subject)
            .outerjoin(Review.relevance)
            .group_by(Review)
            .order_by(desc("total"))
        )

    def get_review_by_id(self, id):
        return session.query(Review).filter(Review.id == id).one_or_none()

    def get_review_by_author_subject(self, author_id, subject):
        return (
            session.query(Review)
            .filter(Review.subject == subject, Review.member_ID == str(author_id))
            .first()
        )

    def update_review(self, id, tier, anonym: bool, text):
        review = Review(id=id, tier=tier, anonym=anonym, text_review=text, date=datetime.date.today())
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
                date=datetime.date.today(),
            )
            session.add(review)
            session.commit()
        except Exception:
            session.rollback()
            raise

    def remove(self, id):
        session.query(Review).filter(Review.id == id).delete()

    def get_votes_count(self, review_id, vote: bool):
        return (
            session.query(ReviewRelevance)
            .filter(ReviewRelevance.review == review_id, ReviewRelevance.vote == vote)
            .count()
        )

    def get_vote_by_author(self, review_id, author):
        return (
            session.query(ReviewRelevance)
            .filter(ReviewRelevance.review == review_id, ReviewRelevance.member_ID == author)
            .first()
        )

    def add_vote(self, review_id, vote: bool, author):
        relevance = ReviewRelevance(member_ID=author, vote=vote, review=review_id)
        session.merge(relevance)
        session.commit()

    def remove_vote(self, review_id, author):
        session.query(ReviewRelevance).filter(
            ReviewRelevance.review == review_id, ReviewRelevance.member_ID == author
        ).delete()

    def get_subject(self, shortcut):
        return session.query(Subject).filter(Subject.shortcut == shortcut)

    def get_subject_details(self, shortcut):
        return (
            session.query(Subject_details)
            .filter(func.lower(Subject_details.shortcut) == shortcut)
            .one_or_none()
        )

    def add_subject(self, shortcut):
        subject = Subject(shortcut=shortcut)
        session.merge(subject)
        session.commit()

    def gen_tierboard_subquery(self, type, sem, degree, year):
        return (
            session.query(Subject.reviews, Subject_details, func.avg(Review.tier).label("avg_tier"))
            .outerjoin(Subject.reviews)
            .group_by(Subject)
            .outerjoin(Subject_details, func.lower(Subject_details.shortcut) == Subject.shortcut)
            .group_by(Subject_details.shortcut)
            .group_by(Review.subject)
            .filter(Subject_details.degree.contains(degree))
            .filter(Subject_details.type.contains(type))
            .filter(Subject_details.semester.contains(sem))
            .filter(Subject_details.year.contains(year))
            .subquery()
        )

    def get_tierboard(self, type, sem, degree, year, offset=0):
        subquery = self.gen_tierboard_subquery(type, sem, degree, year)
        return (
            session.query(subquery.c.shortcut, subquery.c.avg_tier)
            .filter(subquery.c.avg_tier != None)
            .order_by(asc("avg_tier"))
            .offset(offset)
            .limit(10)
            .all()
        )

    def get_tierboard_page_count(self, type, sem, degree, year):
        subquery = self.gen_tierboard_subquery(type, sem, degree, year)
        return math.ceil((
            session.query(subquery.c.shortcut, subquery.c.avg_tier)
            .filter(subquery.c.avg_tier != None)
            .order_by(asc("avg_tier"))
            .count()
        )/10)

    def set_subject_details(self, shortcut, name, credits, semester, end, card, type, for_year, degree):
        subject = Subject_details(
            shortcut=shortcut,
            name=name,
            credits=credits,
            semester=semester,
            end=end,
            card=card,
            type=type,
            year=for_year,
            degree=degree,
        )
        session.merge(subject)
        session.commit()

    def update_subject_type(self, shortcut, type, for_year):
        subject = Subject_details(shortcut=shortcut, type=type, year=for_year)
        session.merge(subject)
        session.commit()

    def update_subject_degree(self, shortcut, degree):
        subject = Subject_details(shortcut=shortcut, degree=degree)
        session.merge(subject)
        session.commit()

    def update_subject_sem(self, shortcut, sem):
        subject = Subject_details(shortcut=shortcut, semester=sem)
        session.merge(subject)
        session.commit()
