from __future__ import annotations

from datetime import datetime
from enum import Enum

from disnake import AuditLogAction
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from database import database, session


class ActionType(Enum):
    kick = AuditLogAction.kick
    ban = AuditLogAction.ban
    unban = AuditLogAction.unban


class ModerationDB(database.base):  # type: ignore
    __tablename__ = "moderation_action_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_id: Mapped[str] = mapped_column(nullable=False)
    author_id: Mapped[str] = mapped_column(nullable=False)
    datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[str] = mapped_column(nullable=True)
    action_type: Mapped[ActionType] = mapped_column(nullable=False)

    @classmethod
    def add_action_log(
        cls, target_id: str, author_id: str, datetime: datetime, reason: str, action_type: ActionType
    ) -> None:
        item = cls(
            target_id=target_id,
            author_id=author_id,
            datetime=datetime,
            reason=reason,
            action_type=action_type,
        )
        session.add(item)
        session.commit()
        return
