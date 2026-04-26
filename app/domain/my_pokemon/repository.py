from __future__ import annotations

from sqlalchemy.orm import selectinload

from app.core.repository.base import BaseRepository
from app.models.my_pokemon import MyPokemon
from app.models.pokemon import Pokemon
from app.models.pokemon_type import PokemonType


class MyPokemonRepository(BaseRepository[MyPokemon]):
    model = MyPokemon
    relations = (
        selectinload(MyPokemon.moves),
        selectinload(MyPokemon.pokemon).selectinload(Pokemon.types),
        selectinload(MyPokemon.pokemon).selectinload(Pokemon.moves),
        selectinload(MyPokemon.pokemon).selectinload(Pokemon.evolutions),
        selectinload(MyPokemon.pokemon).selectinload(Pokemon.growth_rate),
        selectinload(MyPokemon.pokemon)
        .selectinload(Pokemon.types)
        .selectinload(PokemonType.weaknesses),
        selectinload(MyPokemon.pokemon)
        .selectinload(Pokemon.types)
        .selectinload(PokemonType.strengths),
    )
    default_order_by = 'created_at'

    async def create(self, data: dict) -> MyPokemon:
        return await self.save(MyPokemon(**data))
