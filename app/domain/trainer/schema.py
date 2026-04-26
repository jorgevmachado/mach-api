from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import PokedexStatusEnum
from app.domain.pokedex.schema import PokedexSchema
from app.domain.my_pokemon.schema import MyPokemonSchema


class InitializeTrainerRequest(BaseModel):
    pokeballs: int
    capture_rate: int
    pokemon_name: str | None = None


class InitializeTrainerResponse(BaseModel):
    id: UUID
    user_id: UUID
    pokeballs: int
    capture_rate: int
    pokedex_status: PokedexStatusEnum
    pokemon_name: str | None = None
    created_at: datetime

    model_config = {'from_attributes': True}


class TrainerMeResponse(BaseModel):
    id: UUID
    user_id: UUID
    pokeballs: int
    capture_rate: int
    pokedex_status: PokedexStatusEnum
    pokedex_entries: list[PokedexSchema] = []
    my_pokemons: list[MyPokemonSchema] = []
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None

    model_config = {'from_attributes': True}
