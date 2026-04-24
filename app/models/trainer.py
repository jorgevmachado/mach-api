from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models.enums import PokedexStatusEnum
from app.models.user import User

if TYPE_CHECKING:
    from app.models.my_pokemon import MyPokemon
    from app.models.pokedex import Pokedex


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
    pokedex_status: Mapped[PokedexStatusEnum] = mapped_column(
        SAEnum(PokedexStatusEnum, name='pokedexstatusenum'),
        default=PokedexStatusEnum.EMPTY,
        nullable=False,
    )

    # Relationship — not an __init__ parameter
    user: Mapped[User] = relationship(
        'User',
        lazy=default_lazy,
        back_populates='trainer',
        init=False,
    )
    pokedex_entries: Mapped[list['Pokedex']] = relationship(
        'Pokedex',
        back_populates='trainer',
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )
    my_pokemons: Mapped[list['MyPokemon']] = relationship(
        'MyPokemon',
        back_populates='trainer',
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )

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
