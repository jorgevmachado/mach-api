from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PokemonGrowthRateSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    url: str
    name: str
    formula: str
    description: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
