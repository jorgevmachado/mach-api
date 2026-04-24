from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PokemonMoveSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    pp: int
    url: str
    type: str
    name: str
    order: int
    power: int
    target: str
    effect: str
    priority: int
    accuracy: int
    short_effect: str
    damage_class: str
    effect_chance: int | None = None
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
