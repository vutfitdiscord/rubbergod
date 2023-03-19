import json
from typing import List

from sqlalchemy import Boolean, Column, Integer, String

from repository.database import database


class Permit(database.base):
    __tablename__ = "bot_permit"

    login = Column(String, primary_key=True)
    discord_ID = Column(String)


class Valid_person(database.base):
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


class DynamicVerifyRule(database.base):
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
