from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database.base import default_lazy, table_registry
from app.models.associations import (
    pokemon_pokemon_types,
    pokemon_type_strengths,
    pokemon_type_weaknesses,
)

if TYPE_CHECKING:
    from app.models.pokemon import Pokemon

TYPE_COLOR_MAP: dict[str, tuple[str, str]] = {
    'ice': ('#fff', '#51c4e7'),
    'bug': ('#b5d7a7', '#482d53'),
    'fire': ('#fff', '#fd7d24'),
    'rock': ('#fff', '#a38c21'),
    'dark': ('#fff', '#707070'),
    'steel': ('#fff', '#9eb7b8'),
    'ghost': ('#fff', '#7b62a3'),
    'fairy': ('#cb3fa0', '#c8a2c8'),
    'water': ('#6890F0', '#FFFFFF'),
    'grass': ('#78C850', '#FFFFFF'),
    'normal': ('#A8A878', '#FFFFFF'),
    'dragon': ('#fff', '#FF8C00'),
    'poison': ('#fff', '#b97fc9'),
    'flying': ('#424242', '#3dc7ef'),
    'ground': ('#f5f5f5', '#bc5e00'),
    'psychic': ('#fff', '#f366b9'),
    'electric': ('#F8D030', '#212121'),
    'fighting': ('#fff', '#d56723'),
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def resolve_type_colors(name: str) -> tuple[str, str]:
    return TYPE_COLOR_MAP.get(name.strip().lower(), ('#68A090', '#FFFFFF'))


@table_registry.mapped_as_dataclass
class PokemonType:
    __tablename__ = 'pokemon_types'

    url: Mapped[str] = mapped_column(String, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    text_color: Mapped[str] = mapped_column(String, nullable=False, default='')
    background_color: Mapped[str] = mapped_column(String, nullable=False, default='')

    pokemons: Mapped[list['Pokemon']] = relationship(
        'Pokemon',
        secondary=pokemon_pokemon_types,
        back_populates='types',
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )
    weaknesses: Mapped[list['PokemonType']] = relationship(
        'PokemonType',
        secondary=pokemon_type_weaknesses,
        primaryjoin=lambda: PokemonType.id == pokemon_type_weaknesses.c.type_id,
        secondaryjoin=lambda: PokemonType.id == pokemon_type_weaknesses.c.weak_against_id,
        lazy=default_lazy,
        default_factory=list,
        init=False,
    )
    strengths: Mapped[list['PokemonType']] = relationship(
        'PokemonType',
        secondary=pokemon_type_strengths,
        primaryjoin=lambda: PokemonType.id == pokemon_type_strengths.c.type_id,
        secondaryjoin=lambda: PokemonType.id == pokemon_type_strengths.c.strong_against_id,
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

    def __post_init__(self) -> None:
        background, text = resolve_type_colors(self.name)
        if not self.background_color:
            self.background_color = background
        if not self.text_color:
            self.text_color = text
