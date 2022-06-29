from sqlalchemy import Column, String, Integer
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
