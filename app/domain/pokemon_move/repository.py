from __future__ import annotations

from app.core.repository.base import BaseRepository
from app.models.pokemon_move import PokemonMove


class PokemonMoveRepository(BaseRepository[PokemonMove]):
    model = PokemonMove
    default_order_by = 'order'

    async def create(self, data: dict) -> PokemonMove:
        return await self.save(PokemonMove(**data))
