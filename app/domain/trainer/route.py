from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.domain.auth.repository import UserRepository
from app.domain.my_pokemon.repository import MyPokemonRepository
from app.domain.my_pokemon.service import MyPokemonService
from app.domain.pokedex.repository import PokedexRepository
from app.domain.pokedex.service import PokedexService
from app.domain.pokemon_ability.repository import PokemonAbilityRepository
from app.domain.pokemon_growth_rate.repository import PokemonGrowthRateRepository
from app.domain.pokemon_move.repository import PokemonMoveRepository
from app.domain.pokemon.repository import PokemonRepository
from app.domain.pokemon_type.repository import PokemonTypeRepository
from app.domain.pokemon.service import PokemonService
from app.domain.trainer.repository import TrainerRepository
from app.domain.trainer.schema import (
    TrainerInitializeResultSchema,
    TrainerInitializeSchema,
    TrainerMeSchema,
)
from app.domain.trainer.service import TrainerService
from app.infrastructure.external_api.pokeapi_client import PokeApiClient
from app.models.user import User

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def get_trainer_service(session: Session) -> TrainerService:
    trainer_repository = TrainerRepository(session)
    pokedex_service = PokedexService(
        repository=PokedexRepository(session),
        pokemon_repository=PokemonRepository(session),
        trainer_repository=trainer_repository,
    )
    pokemon_service = PokemonService(
        repository=PokemonRepository(session),
        move_repository=PokemonMoveRepository(session),
        ability_repository=PokemonAbilityRepository(session),
        type_repository=PokemonTypeRepository(session),
        growth_rate_repository=PokemonGrowthRateRepository(session),
        pokeapi_client=PokeApiClient(),
    )
    return TrainerService(
        trainer_repository=trainer_repository,
        user_repository=UserRepository(session),
        pokemon_service=pokemon_service,
        my_pokemon_service=MyPokemonService(MyPokemonRepository(session), pokedex_service),
        pokedex_service=pokedex_service,
    )


def get_trainer_repository(session: Session) -> TrainerRepository:
    return TrainerRepository(session)


@router.post(
    '/initialize',
    response_model=TrainerInitializeResultSchema,
    status_code=HTTPStatus.CREATED,
)
async def initialize_trainer(
    data: TrainerInitializeSchema,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrainerService, Depends(get_trainer_service)],
):
    trainer = await service.initialize(current_user.id, data)
    return trainer


@router.get('/me', response_model=TrainerMeSchema, status_code=HTTPStatus.OK)
async def me_trainer(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrainerService, Depends(get_trainer_service)],
):
    return await service.get_me(current_user)
