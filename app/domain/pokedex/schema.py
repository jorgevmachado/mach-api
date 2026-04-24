from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.pokemon.schema import PokemonSchema, PokemonSummarySchema
from app.domain.pokemon_type.schema import PokemonTypeRelationSchema
from app.shared.schemas import FilterPage


class PokedexPokemonListSchema(PokemonSummarySchema):
    model_config = ConfigDict(from_attributes=True)

    types: list[PokemonTypeRelationSchema] = []


class PokedexProgressionFields(BaseModel):
    hp: int
    iv_hp: int
    ev_hp: int
    wins: int
    level: int
    losses: int
    max_hp: int
    battles: int
    speed: int
    iv_speed: int
    ev_speed: int
    attack: int
    iv_attack: int
    ev_attack: int
    defense: int
    iv_defense: int
    ev_defense: int
    experience: int
    special_attack: int
    iv_special_attack: int
    ev_special_attack: int
    special_defense: int
    iv_special_defense: int
    ev_special_defense: int
    discovered: bool
    formula: str


class PokedexSchema(PokedexProgressionFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pokemon: PokedexPokemonListSchema
    trainer_id: UUID
    pokemon_id: UUID
    discovered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class PokedexDetailSchema(PokedexProgressionFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pokemon: PokemonSchema
    trainer_id: UUID
    pokemon_id: UUID
    discovered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class PokedexUpdateSchema(BaseModel):
    hp: int | None = Field(default=None, ge=0)
    wins: int | None = Field(default=None, ge=0)
    level: int | None = Field(default=None, ge=1)
    losses: int | None = Field(default=None, ge=0)
    max_hp: int | None = Field(default=None, ge=0)
    battles: int | None = Field(default=None, ge=0)
    speed: int | None = Field(default=None, ge=0)
    attack: int | None = Field(default=None, ge=0)
    defense: int | None = Field(default=None, ge=0)
    experience: int | None = Field(default=None, ge=0)
    special_attack: int | None = Field(default=None, ge=0)
    special_defense: int | None = Field(default=None, ge=0)
    discovered: bool | None = None


class PokedexFilterPageSchema(FilterPage):
    pokemon_name: str | None = None
    discovered: bool | None = None
