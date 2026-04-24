from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models.pokemon_ability import PokemonAbility


class PokemonAbilityRepository(BaseRepository[PokemonAbility]):
    model = PokemonAbility
    default_order_by = 'order'

    async def create(self, data: dict) -> PokemonAbility:
        return await self.save(PokemonAbility(**data))
