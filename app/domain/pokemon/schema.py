from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import StatusEnum
from app.shared.schemas import FilterPage


class PokemonRelatedNameSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class PokemonSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    order: int
    status: StatusEnum
    external_image: str
    hp: int | None = None
    image: str | None = None
    speed: int | None = None
    height: int | None = None
    weight: int | None = None
    attack: int | None = None
    defense: int | None = None
    habitat: str | None = None
    is_baby: bool | None = None
    shape_url: str | None = None
    shape_name: str | None = None
    is_mythical: bool | None = None
    gender_rate: int | None = None
    is_legendary: bool | None = None
    capture_rate: int | None = None
    hatch_counter: int | None = None
    base_happiness: int | None = None
    special_attack: int | None = None
    base_experience: int | None = None
    special_defense: int | None = None
    evolution_chain: str | None = None
    evolves_from_species: str | None = None
    has_gender_differences: bool | None = None
    growth_rate: PokemonRelatedNameSchema | None = None
    moves: list[PokemonRelatedNameSchema] = []
    abilities: list[PokemonRelatedNameSchema] = []
    types: list[PokemonRelatedNameSchema] = []
    evolutions: list[PokemonRelatedNameSchema] = []
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None


class PokemonFilterPageSchema(FilterPage):
    name: str | None = None
    order: int | None = Field(default=None, ge=0)
