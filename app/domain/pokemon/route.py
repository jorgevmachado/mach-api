from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination.schemas import CustomLimitOffsetPage
from app.core.security import get_current_user
from app.domain.pokemon.repository import PokemonRepository
from app.domain.pokemon.schema import PokemonFilterPageSchema, PokemonSchema
from app.domain.pokemon.service import PokemonService
from app.domain.pokemon_ability.repository import PokemonAbilityRepository
from app.domain.pokemon_ability.schema import PokemonAbilitySchema
from app.domain.pokemon_ability.service import PokemonAbilityService
from app.domain.pokemon_growth_rate.repository import PokemonGrowthRateRepository
from app.domain.pokemon_growth_rate.schema import PokemonGrowthRateSchema
from app.domain.pokemon_growth_rate.service import PokemonGrowthRateService
from app.domain.pokemon_move.repository import PokemonMoveRepository
from app.domain.pokemon_move.schema import PokemonMoveSchema
from app.domain.pokemon_move.service import PokemonMoveService
from app.domain.pokemon_type.repository import PokemonTypeRepository
from app.domain.pokemon_type.schema import PokemonTypeSchema
from app.domain.pokemon_type.service import PokemonTypeService
from app.infrastructure.external_api.pokeapi_client import PokeApiClient
from app.models.user import User

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def get_poke_api_client() -> PokeApiClient:
    return PokeApiClient()


def get_pokemon_service(
    session: Session,
    pokeapi_client: Annotated[PokeApiClient, Depends(get_poke_api_client)],
) -> PokemonService:
    return PokemonService(
        repository=PokemonRepository(session),
        move_repository=PokemonMoveRepository(session),
        ability_repository=PokemonAbilityRepository(session),
        type_repository=PokemonTypeRepository(session),
        growth_rate_repository=PokemonGrowthRateRepository(session),
        pokeapi_client=pokeapi_client,
    )


def get_pokemon_move_service(session: Session) -> PokemonMoveService:
    return PokemonMoveService(PokemonMoveRepository(session))


def get_pokemon_ability_service(session: Session) -> PokemonAbilityService:
    return PokemonAbilityService(PokemonAbilityRepository(session))


def get_pokemon_type_service(session: Session) -> PokemonTypeService:
    return PokemonTypeService(PokemonTypeRepository(session))


def get_pokemon_growth_rate_service(session: Session) -> PokemonGrowthRateService:
    return PokemonGrowthRateService(PokemonGrowthRateRepository(session))


@router.get('', response_model=CustomLimitOffsetPage[PokemonSchema], status_code=HTTPStatus.OK)
async def list_pokemon(
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[PokemonService, Depends(get_pokemon_service)],
    page_filter: Annotated[PokemonFilterPageSchema, Depends()],
):
    filter_page = page_filter.with_updates(page=page_filter.page or 1, limit=page_filter.limit or 12)
    return await service.list_cached(page_filter=filter_page)


@router.get('/moves', response_model=list[PokemonMoveSchema], status_code=HTTPStatus.OK)
async def list_moves(
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[PokemonMoveService, Depends(get_pokemon_move_service)],
):
    return await service.list_all()


@router.get('/abilities', response_model=list[PokemonAbilitySchema], status_code=HTTPStatus.OK)
async def list_abilities(
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[PokemonAbilityService, Depends(get_pokemon_ability_service)],
):
    return await service.list_all()


@router.get('/types', response_model=list[PokemonTypeSchema], status_code=HTTPStatus.OK)
async def list_types(
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[PokemonTypeService, Depends(get_pokemon_type_service)],
):
    return await service.list_all()


@router.get(
    '/growth-rates',
    response_model=list[PokemonGrowthRateSchema],
    status_code=HTTPStatus.OK,
)
async def list_growth_rates(
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[
        PokemonGrowthRateService, Depends(get_pokemon_growth_rate_service)
    ],
):
    return await service.list_all()


@router.get(
    '/{name_or_id}',
    response_model=PokemonSchema,
    status_code=HTTPStatus.OK,
)
async def get_pokemon(
    name_or_id: str,
    _: Annotated[User, Depends(get_current_user)],
    service: Annotated[PokemonService, Depends(get_pokemon_service)],
):
    return await service.get(name_or_id)
