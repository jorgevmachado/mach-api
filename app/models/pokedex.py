from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry

if TYPE_CHECKING:
    from app.models.pokemon import Pokemon
    from app.models.trainer import Trainer


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@table_registry.mapped_as_dataclass
class Pokedex:
    __tablename__ = 'pokedex'
    __table_args__ = (
        UniqueConstraint('trainer_id', 'pokemon_id', name='uq_pokedex_trainer_pokemon'),
    )

    hp: Mapped[int] = mapped_column(Integer, nullable=False)
    max_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    speed: Mapped[int] = mapped_column(Integer, nullable=False)
    attack: Mapped[int] = mapped_column(Integer, nullable=False)
    defense: Mapped[int] = mapped_column(Integer, nullable=False)
    special_attack: Mapped[int] = mapped_column(Integer, nullable=False)
    special_defense: Mapped[int] = mapped_column(Integer, nullable=False)
    formula: Mapped[str] = mapped_column(String, nullable=False)
    pokemon_id: Mapped[UUID] = mapped_column(ForeignKey('pokemons.id'), nullable=False)
    trainer_id: Mapped[UUID] = mapped_column(ForeignKey('trainers.id'), nullable=False)
    iv_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ev_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    battles: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    iv_speed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ev_speed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    iv_attack: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ev_attack: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    iv_defense: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ev_defense: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    iv_special_attack: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ev_special_attack: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    iv_special_defense: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ev_special_defense: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discovered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    pokemon: Mapped['Pokemon'] = relationship(
        'Pokemon',
        back_populates='pokedex_entries',
        lazy=default_lazy,
        init=False,
    )
    trainer: Mapped['Trainer'] = relationship(
        'Trainer',
        back_populates='pokedex_entries',
        lazy=default_lazy,
        init=False,
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid4, init=False)
    discovered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default_factory=_utcnow, init=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
