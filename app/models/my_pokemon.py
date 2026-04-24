from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models.associations import my_pokemon_pokemon_moves

if TYPE_CHECKING:
    from app.models.pokemon import Pokemon
    from app.models.pokemon_move import PokemonMove
    from app.models.trainer import Trainer


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@table_registry.mapped_as_dataclass
class MyPokemon:
    __tablename__ = 'my_pokemons'

    hp: Mapped[int] = mapped_column(Integer, nullable=False)
    max_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    nickname: Mapped[str] = mapped_column(String, nullable=False)
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

    pokemon: Mapped['Pokemon'] = relationship(
        'Pokemon',
        back_populates='my_pokemons',
        lazy=default_lazy,
        init=False,
    )
    trainer: Mapped['Trainer'] = relationship(
        'Trainer',
        back_populates='my_pokemons',
        lazy=default_lazy,
        init=False,
    )
    moves: Mapped[list['PokemonMove']] = relationship(
        'PokemonMove',
        secondary=my_pokemon_pokemon_moves,
        back_populates='my_pokemons',
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default_factory=uuid4, init=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default_factory=_utcnow, init=False
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
