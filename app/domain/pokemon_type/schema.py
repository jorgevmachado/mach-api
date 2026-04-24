from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PokemonTypeRelationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str


class PokemonTypeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    order: int
    name: str
    text_color: str
    background_color: str
    weaknesses: list[PokemonTypeRelationSchema] = []
    strengths: list[PokemonTypeRelationSchema] = []
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
