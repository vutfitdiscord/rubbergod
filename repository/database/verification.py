from __future__ import annotations

import json
from enum import IntEnum
from typing import List, Optional

from sqlalchemy import Boolean, Column, Integer, String, asc, exists

from repository.database import database, session


class VerifyStatus(IntEnum):
    """ Common enum to verification states. """
    Verified = 0
    Unverified = 1
    InProcess = 2


class PermitDB(database.base):
    __tablename__ = "bot_permit"

    login = Column(String, primary_key=True)
    discord_ID = Column(String)


class ValidPersonDB(database.base):
    __tablename__ = "bot_valid_persons"
    # Status 0 = verified
    # Status 1 = unverified
    # Status 2 = in process of verification (code sent)

    login = Column(String, primary_key=True)
    name = Column(String)
    year = Column(String)
    code = Column(String)
    status = Column(Integer, default=1)
    mail = Column(String)

    def get_mail(self, fallback_domain: str) -> str:
        if self.mail is not None and len(self.mail) > 0:
            return self.mail

        if len(fallback_domain) == 0:
            raise Exception(
                "The user does not have an e-mail address set "
                + "up and a fallback domain has not been provided."
            )

        return f"{self.login}@{fallback_domain}"  # fallback

    @classmethod
    def get_user(cls, login: str, status: int = 2) -> Optional[ValidPersonDB]:
        """"Finds login from database"""
        user = (
            session.query(ValidPersonDB)
            .filter(ValidPersonDB.login == login, ValidPersonDB.status == status)
            .one_or_none()
        )
        return user

    @classmethod
    def add_user(cls, login: str, year: str, status: int = 1) -> ValidPersonDB:
        """Add user to database"""
        person = ValidPersonDB(login=login, year=year, status=status)
        session.add(person)
        session.commit()
        return person

    @classmethod
    def get_user_by_login(cls, login: str) -> Optional[ValidPersonDB]:
        """Finds login from DB (without status check)"""
        user = (
            session.query(ValidPersonDB).filter(ValidPersonDB.login == login).one_or_none()
        )

        return user

    def save_verified(self, discord_id: str) -> None:
        """"Inserts login with discord name into database"""
        session.add(PermitDB(login=self.login, discord_ID=discord_id))
        self.status = 0
        session.commit()

    @classmethod
    def get_user_by_id(self, discord_ID: str) -> Optional[ValidPersonDB]:
        """Returns user specified by discord ID"""
        return (
            session.query(ValidPersonDB)
            .outerjoin(PermitDB, PermitDB.login == ValidPersonDB.login)
            .filter(PermitDB.discord_ID == str(discord_ID))
            .one_or_none()
        )

    def save_sent_code(self, code: str) -> None:
        """Updates a specified login with a new verification code"""
        self.code = code
        self.status = 2
        session.commit()


class DynamicVerifyDB(database.base):
    __tablename__ = "dynamic_verify_rules"

    id = Column(String, primary_key=True)
    name = Column(String, index=True, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    mod_check = Column(Boolean, default=True, nullable=False)
    role_ids = Column(String, nullable=False, default="[]")

    def get_role_ids(self) -> List[int]:
        data = json.loads(self.role_ids)
        return [int(item) for item in data]

    def set_role_ids(self, roles: List[int]) -> None:
        self.role_ids = json.dumps(roles)

    def update_rule(self) -> None:
        session.merge(self)
        session.commit()

    def remove_rule(self) -> None:
        session.delete(self)
        session.commit()

    @classmethod
    def exists_rule(cls, rule: str) -> bool:
        return session.query(
            exists().where(cls.id == rule and cls.enabled)
        ).scalar()

    @classmethod
    def get_rule(cls, rule: str) -> Optional[DynamicVerifyDB]:
        return (
            session.query(cls)
            .filter(cls.id == rule)
            .one_or_none()
        )

    @classmethod
    def get_rules(cls, limit: int) -> List[DynamicVerifyDB]:
        return session.query(cls).order_by(asc("id")).limit(limit).all()
