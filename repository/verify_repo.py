from repository.base_repository import BaseRepository
from sqlalchemy.sql import exists
from sqlalchemy import asc
from repository.database import session
from repository.database.verification import DynamicVerifyRule
from typing import List, Union


class VerifyRepository(BaseRepository):
    def exists_rule(self, rule: str) -> bool:
        return session.query(
            exists().where(
                DynamicVerifyRule.id == rule and DynamicVerifyRule.enabled
            )
        ).scalar()

    def get_rule(self, rule: str) -> Union[DynamicVerifyRule, None]:
        return (
            session.query(DynamicVerifyRule)
            .filter(DynamicVerifyRule.id == rule)
            .one_or_none()
        )

    def get_rules(self, limit: int) -> List[DynamicVerifyRule]:
        return session.query(DynamicVerifyRule).order_by(asc("id")).limit(limit).all()
