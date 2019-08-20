from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.verification import Permit, Valid_person


class UserRepository(BaseRepository):
    # Status 0 = verified
    # Status 1 = unverified
    # Status 2 = in process of verification (code sent)

    def save_sent_code(self, login: str, code: str):
        """Updates a specified login with a new verification code"""
        person = session.query(Valid_person).\
            filter(Valid_person.login == login).one_or_none()
        person.code = code
        person.status = 2
        session.commit()

    def save_verified(self, login: str, discord_id: str):
        """"Inserts login with discord name into database"""
        session.add(Permit(login=login, discord_ID=discord_id))

        person = session.query(Valid_person).\
            filter(Valid_person.login == login).one_or_none()
        person.status = 0

        session.commit()

    def has_unverified_login(self, login: str):
        """"Checks if there's a login """
        query = session.query(Valid_person).\
            filter(Valid_person.login == login and Valid_person.status == 1).\
            one_or_none()
        return True if query is not None else False

    def get_user(self, login: str, status: int = 2):
        """"Finds login from database"""
        user = session.query(Valid_person).\
            filter(Valid_person.login == login and
                   Valid_person.status == status).\
            one_or_none()
        return user

    def add_user(self, login: str, year: str, status: int = 1):
        """"Finds login from database"""
        session.add(Valid_person(login=login, year=year, status=status))
        session.commit()
