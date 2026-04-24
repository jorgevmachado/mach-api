from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models.pokemon_growth_rate import PokemonGrowthRate


class PokemonGrowthRateRepository(BaseRepository[PokemonGrowthRate]):
    model = PokemonGrowthRate
    default_order_by = 'name'

    async def create(self, data: dict) -> PokemonGrowthRate:
        return await self.save(PokemonGrowthRate(**data))
