from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models.associations import (
    pokemon_evolutions,
    pokemon_pokemon_abilities,
    pokemon_pokemon_moves,
    pokemon_pokemon_types,
)
from app.models.enums import StatusEnum

if TYPE_CHECKING:
    from app.models.my_pokemon import MyPokemon
    from app.models.pokedex import Pokedex
    from app.models.pokemon_ability import PokemonAbility
    from app.models.pokemon_growth_rate import PokemonGrowthRate
    from app.models.pokemon_move import PokemonMove
    from app.models.pokemon_type import PokemonType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@table_registry.mapped_as_dataclass
class Pokemon:
    __tablename__ = 'pokemons'

    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    external_image: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[StatusEnum] = mapped_column(
        SAEnum(StatusEnum, name='statusenum'),
        nullable=False,
    )
    hp: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    image: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    speed: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    weight: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    attack: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    defense: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    habitat: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    is_baby: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    shape_url: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    shape_name: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    is_mythical: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    gender_rate: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    is_legendary: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=False)
    capture_rate: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    hatch_counter: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    base_happiness: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    special_attack: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    base_experience: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    special_defense: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    evolution_chain: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    evolves_from_species: Mapped[str | None] = mapped_column(
        String, nullable=True, default=None
    )
    has_gender_differences: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, default=False
    )
    growth_rate_id: Mapped[UUID | None] = mapped_column(
        ForeignKey('pokemon_growth_rates.id'), nullable=True, default=None
    )

    growth_rate: Mapped['PokemonGrowthRate | None'] = relationship(
        'PokemonGrowthRate',
        back_populates='pokemons',
        lazy=default_lazy,
        init=False,
    )
    moves: Mapped[list['PokemonMove']] = relationship(
        'PokemonMove',
        secondary=pokemon_pokemon_moves,
        back_populates='pokemons',
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )
    abilities: Mapped[list['PokemonAbility']] = relationship(
        'PokemonAbility',
        secondary=pokemon_pokemon_abilities,
        back_populates='pokemons',
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )
    types: Mapped[list['PokemonType']] = relationship(
        'PokemonType',
        secondary=pokemon_pokemon_types,
        back_populates='pokemons',
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )
    evolutions: Mapped[list['Pokemon']] = relationship(
        'Pokemon',
        secondary=pokemon_evolutions,
        primaryjoin=lambda: Pokemon.id == pokemon_evolutions.c.pokemon_id,
        secondaryjoin=lambda: Pokemon.id == pokemon_evolutions.c.evolution_id,
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )
    pokedex_entries: Mapped[list['Pokedex']] = relationship(
        'Pokedex',
        back_populates='pokemon',
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )
    my_pokemons: Mapped[list['MyPokemon']] = relationship(
        'MyPokemon',
        back_populates='pokemon',
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )

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
