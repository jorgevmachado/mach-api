from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@table_registry.mapped_as_dataclass
class Trainer:
    __tablename__ = 'trainers'
    __table_args__ = (UniqueConstraint('user_id', name='uq_trainers_user_id'),)

    # Required fields (no defaults)
    user_id: Mapped[UUID] = mapped_column(ForeignKey('users.id'), nullable=False)
    capture_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    pokeballs: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationship — not an __init__ parameter
    user: Mapped[User] = relationship('User', lazy=default_lazy, init=False)

    # Auto-generated / server-managed — excluded from __init__
    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid4, init=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default_factory=_utcnow, init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
