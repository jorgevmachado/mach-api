from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.core.repository.base import BaseRepository
from app.models.pokemon import Pokemon
from app.models.pokemon_type import PokemonType


class PokemonRepository(BaseRepository[Pokemon]):
    model = Pokemon
    relations = (
        selectinload(Pokemon.growth_rate),
        selectinload(Pokemon.moves),
        selectinload(Pokemon.abilities),
        selectinload(Pokemon.types).selectinload(PokemonType.weaknesses),
        selectinload(Pokemon.types).selectinload(PokemonType.strengths),
        selectinload(Pokemon.evolutions),
    )
    default_order_by = 'order'

    async def create(self, data: dict) -> Pokemon:
        return await self.save(Pokemon(**data))
