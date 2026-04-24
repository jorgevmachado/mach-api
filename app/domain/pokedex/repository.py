from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.core.repository.base import BaseRepository
from app.models.pokedex import Pokedex
from app.models.pokemon import Pokemon
from app.models.pokemon_type import PokemonType


class PokedexRepository(BaseRepository[Pokedex]):
    model = Pokedex
    relations = (
        selectinload(Pokedex.pokemon).selectinload(Pokemon.types),
        selectinload(Pokedex.pokemon).selectinload(Pokemon.moves),
        selectinload(Pokedex.pokemon).selectinload(Pokemon.evolutions),
        selectinload(Pokedex.pokemon)
        .selectinload(Pokemon.types)
        .selectinload(PokemonType.weaknesses),
        selectinload(Pokedex.pokemon)
        .selectinload(Pokemon.types)
        .selectinload(PokemonType.strengths),
        selectinload(Pokedex.pokemon).selectinload(Pokemon.growth_rate),
    )
    default_order_by = 'pokemon.order'

    async def create(self, data: dict) -> Pokedex:
        return await self.save(Pokedex(**data))
