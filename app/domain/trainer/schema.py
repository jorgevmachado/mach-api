from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.my_pokemon.schema import MyPokemonSchema
from app.domain.pokedex.schema import PokedexSchema
from app.models.enums import PokedexStatusEnum


class TrainerInitializeSchema(BaseModel):
    pokeballs: int
    capture_rate: int
    pokemon_name: str | None = None


class TrainerInitializeResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    pokeballs: int
    capture_rate: int
    pokedex_status: PokedexStatusEnum
    pokemon_name: str | None = None
    message: str | None = None
    created_at: datetime


class TrainerMeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
