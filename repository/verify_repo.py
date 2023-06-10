from typing import List, Union

from sqlalchemy import asc
from sqlalchemy.sql import exists

from repository.base_repository import BaseRepository
from repository.database import session
from repository.database.verification import DynamicVerifyRule


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

    def update_rule(self, rule: DynamicVerifyRule) -> None:
        session.merge(rule)
        session.commit()

    def remove_rule(self, rule: DynamicVerifyRule) -> None:
        session.query(DynamicVerifyRule).filter(DynamicVerifyRule.id == rule.id).delete()
        session.commit()
