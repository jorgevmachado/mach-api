from __future__ import annotations

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.pagination.schemas import CustomLimitOffsetPage
from app.core.security import get_current_user
from app.domain.pokedex.repository import PokedexRepository
from app.domain.pokedex.schema import (
    PokedexDetailSchema,
    PokedexFilterPageSchema,
    PokedexSchema,
    PokedexUpdateSchema,
)
from app.domain.pokedex.service import PokedexService
from app.domain.pokemon.repository import PokemonRepository
from app.domain.trainer.repository import TrainerRepository
from app.models.trainer import Trainer
from app.models.user import User

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def get_pokedex_service(session: Session) -> PokedexService:
    trainer_repository = TrainerRepository(session)
    return PokedexService(
        repository=PokedexRepository(session),
        pokemon_repository=PokemonRepository(session),
        trainer_repository=trainer_repository,
    )


async def get_current_trainer(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Session,
) -> Trainer:
    trainer = await TrainerRepository(session).get_by_user_id(current_user.id)
    if trainer is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Trainer not found')
    return trainer


@router.get('', response_model=CustomLimitOffsetPage[PokedexSchema], status_code=HTTPStatus.OK)
async def list_pokedex(
    trainer: Annotated[Trainer, Depends(get_current_trainer)],
    service: Annotated[PokedexService, Depends(get_pokedex_service)],
    page_filter: Annotated[PokedexFilterPageSchema, Depends()],
):
    filter_page = page_filter.with_updates(page=page_filter.page or 1, limit=page_filter.limit or 12)
    return await service.list_trainer(trainer.id, filter_page)


@router.get('/{entry_id}', response_model=PokedexDetailSchema, status_code=HTTPStatus.OK)
async def get_pokedex(
    entry_id: str,
    trainer: Annotated[Trainer, Depends(get_current_trainer)],
    service: Annotated[PokedexService, Depends(get_pokedex_service)],
):
    return await service.get_trainer(entry_id, trainer.id)


@router.put('/{entry_id}', response_model=PokedexSchema, status_code=HTTPStatus.OK)
async def update_pokedex(
    entry_id: str,
    data: PokedexUpdateSchema,
    trainer: Annotated[Trainer, Depends(get_current_trainer)],
    service: Annotated[PokedexService, Depends(get_pokedex_service)],
):
    return await service.update_trainer(entry_id, trainer.id, data)


@router.delete('/{entry_id}', status_code=HTTPStatus.OK)
async def delete_pokedex(
    entry_id: str,
    trainer: Annotated[Trainer, Depends(get_current_trainer)],
    service: Annotated[PokedexService, Depends(get_pokedex_service)],
):
    return await service.soft_delete_trainer(entry_id, trainer.id)
