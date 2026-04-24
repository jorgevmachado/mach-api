from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.pokemon.schema import PokemonSchema, PokemonSummarySchema
from app.domain.pokemon_move.schema import PokemonMoveSchema
from app.domain.pokemon_type.schema import PokemonTypeRelationSchema
from app.shared.schemas import FilterPage


class MyPokemonPokemonListSchema(PokemonSummarySchema):
    model_config = ConfigDict(from_attributes=True)

    types: list[PokemonTypeRelationSchema] = []


class MyPokemonProgressionFields(BaseModel):
    hp: int
    iv_hp: int
    ev_hp: int
    wins: int
    level: int
    losses: int
    max_hp: int
    battles: int
    nickname: str
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
    formula: str


class MyPokemonSchema(MyPokemonProgressionFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pokemon: MyPokemonPokemonListSchema
    trainer_id: UUID
    pokemon_id: UUID
    captured_at: datetime
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class MyPokemonDetailSchema(MyPokemonProgressionFields):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pokemon: PokemonSchema
    moves: list[PokemonMoveSchema] = []
    trainer_id: UUID
    pokemon_id: UUID
    captured_at: datetime
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class MyPokemonUpdateSchema(BaseModel):
    nickname: str

    @field_validator('nickname')
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 3:
            raise ValueError('Nickname must be at least 3 characters')
        return trimmed


class MyPokemonFilterPageSchema(FilterPage):
    nickname: str | None = None
    pokemon_name: str | None = None
