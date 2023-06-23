from __future__ import annotations

import json
from typing import List, Union

from sqlalchemy import Boolean, Column, Integer, String, asc, exists

from repository.database import database, session


class PermitDB(database.base):
    __tablename__ = "bot_permit"

    login = Column(String, primary_key=True)
    discord_ID = Column(String)


class ValidPersonDB(database.base):
    __tablename__ = "bot_valid_persons"

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
    def get_rule(cls, rule: str) -> Union[DynamicVerifyDB, None]:
        return (
            session.query(cls)
            .filter(cls.id == rule)
            .one_or_none()
        )

    @classmethod
    def get_rules(cls, limit: int) -> List[DynamicVerifyDB]:
        return session.query(cls).order_by(asc("id")).limit(limit).all()
