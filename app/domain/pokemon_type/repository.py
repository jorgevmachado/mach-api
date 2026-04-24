from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.core.repository.base import BaseRepository
from app.models.pokemon_type import PokemonType


class PokemonTypeRepository(BaseRepository[PokemonType]):
    model = PokemonType
    relations = (
        selectinload(PokemonType.weaknesses),
        selectinload(PokemonType.strengths),
    )
    default_order_by = 'order'

    async def create(self, data: dict) -> PokemonType:
        return await self.save(PokemonType(**data))
