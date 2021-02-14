from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.verification import Permit, Valid_person
from enum import IntEnum


class VerifyStatus(IntEnum):
    """ Common enum to verification states. """
    Verified = 0
    Unverified = 1
    InProcess = 2


class UserRepository(BaseRepository):
    # Status 0 = verified
    # Status 1 = unverified
    # Status 2 = in process of verification (code sent)

    def save_sent_code(self, login: str, code: str):
        """Updates a specified login with a new verification code"""
        person = session.query(Valid_person).filter(Valid_person.login == login).one_or_none()
        person.code = code
        person.status = 2
        session.commit()

    def save_verified(self, login: str, discord_id: str):
        """"Inserts login with discord name into database"""
        session.add(Permit(login=login, discord_ID=discord_id))

        person = session.query(Valid_person).filter(Valid_person.login == login).one_or_none()
        person.status = 0

        session.commit()

    def get_user(self, login: str, status: int = 2):
        """"Finds login from database"""
        user = (
            session.query(Valid_person)
            .filter(Valid_person.login == login, Valid_person.status == status)
            .one_or_none()
        )
        return user

    def get_user_by_id(self, discord_ID):
        """Returns user specified by discord ID"""
        return (
            session.query(Valid_person)
            .outerjoin(Permit, Permit.login == Valid_person.login)
            .filter(Permit.discord_ID == str(discord_ID))
            .one_or_none()
        )

    def add_user(self, login: str, year: str, status: int = 1):
        """Add user to database"""
        session.add(Valid_person(login=login, year=year, status=status))
        session.commit()

    def get_user_by_login(self, login: str):
        """Finds login from DB (without status check)"""
        user = (
            session.query(Valid_person).filter(Valid_person.login == login).one_or_none()
        )

        return user
