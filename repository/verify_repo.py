from repository.base_repository import BaseRepository
from sqlalchemy.sql import exists
from repository.database import session
from repository.database.verification import DynamicVerifyRule
from typing import Union


class VerifyRepository(BaseRepository):
    def exists_rule(self, rule: str) -> bool:
        return session.query(exists().where(DynamicVerifyRule.id == rule)).scalar()

    def get_rule(self, rule: str) -> Union[DynamicVerifyRule, None]:
        return session.query(DynamicVerifyRule).filter(DynamicVerifyRule.id == rule).one_or_none()

    def increment_rule_use(self, rule: DynamicVerifyRule):
        rule.use_count += 1
        session.commit()
