from __future__ import annotations

import logging
import random
from http import HTTPStatus
from uuid import UUID

from fastapi import BackgroundTasks
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.database import engine
from app.core.exceptions import handle_service_exception
from app.domain.auth.repository import UserRepository
from app.domain.my_pokemon.service import MyPokemonService
from app.domain.pokedex.service import PokedexService
from app.domain.pokemon.service import PokemonService
from app.domain.trainer.repository import TrainerRepository
from app.domain.trainer.schema import InitializeTrainerRequest, InitializeTrainerResponse
from app.models.enums import PokedexStatusEnum, StatusEnum

logger = logging.getLogger(__name__)


async def run_pokedex_initialization_task(
    trainer_id: UUID,
    starter_name: str,
) -> None:
    from app.domain.pokedex.repository import PokedexRepository
    from app.domain.pokemon.repository import PokemonRepository
    from app.domain.trainer.repository import TrainerRepository

    async with AsyncSession(engine, expire_on_commit=False) as session:
        trainer_repository = TrainerRepository(session)
        pokedex_service = PokedexService(
            repository=PokedexRepository(session),
            pokemon_repository=PokemonRepository(session),
            trainer_repository=trainer_repository,
        )

        try:
            await pokedex_service.initialize_for_trainer(trainer_id, starter_name)
            await trainer_repository.update_pokedex_status(trainer_id, PokedexStatusEnum.READY)
        except Exception:
            await session.rollback()
            await trainer_repository.update_pokedex_status(trainer_id, PokedexStatusEnum.FAILED)


class TrainerService:
    def __init__(
        self,
        trainer_repository: TrainerRepository,
        user_repository: UserRepository,
        pokemon_service: PokemonService,
        my_pokemon_service: MyPokemonService,
        pokedex_service: PokedexService,
    ) -> None:
        self.trainer_repository = trainer_repository
        self.user_repository = user_repository
        self.pokemon_service = pokemon_service
        self.my_pokemon_service = my_pokemon_service
        self.pokedex_service = pokedex_service

    async def _resolve_starter(self, pokemon_name: str | None = None):
        await self.pokemon_service.list_sync()
        if pokemon_name:
            pokemon = await self.pokemon_service.repository.find_by(name=pokemon_name)
            if pokemon is None:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail='Requested starter pokemon not found',
                )
            return pokemon

        pokemons = await self.pokemon_service.repository.list_all()
        complete_pokemons = [pokemon for pokemon in pokemons if pokemon.status == StatusEnum.COMPLETE]
        source = complete_pokemons or pokemons
        if not source:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail='Pokemon catalog is not initialized',
            )
        return random.choice(source)

    async def initialize(
        self,
        user_id: UUID,
        data: InitializeTrainerRequest,
        background_tasks: BackgroundTasks | None = None,
    ) -> InitializeTrainerResponse:
        try:
            existing = await self.trainer_repository.get_by_user_id(user_id)
            if existing:
                starter = next(iter(existing.my_pokemons), None)
                if existing.pokedex_status in (PokedexStatusEnum.EMPTY, PokedexStatusEnum.FAILED):
                    await self.trainer_repository.update_pokedex_status(
                        existing.id,
                        PokedexStatusEnum.INITIALIZING,
                    )
                    if starter is not None:
                        if background_tasks is not None:
                            background_tasks.add_task(
                                run_pokedex_initialization_task,
                                existing.id,
                                starter.pokemon.name,
                            )
                        else:
                            await run_pokedex_initialization_task(existing.id, starter.pokemon.name)
                    existing.pokedex_status = PokedexStatusEnum.INITIALIZING

                return InitializeTrainerResponse(
                    id=existing.id,
                    user_id=existing.user_id,
                    pokeballs=existing.pokeballs,
                    capture_rate=existing.capture_rate,
                    pokedex_status=existing.pokedex_status,
                    pokemon_name=starter.pokemon.name if starter is not None else None,
                    created_at=existing.created_at,
                )

            starter = await self._resolve_starter(data.pokemon_name)

            trainer = await self.trainer_repository.create(
                {
                    'user_id': user_id,
                    'pokeballs': data.pokeballs,
                    'capture_rate': data.capture_rate,
                    'pokedex_status': PokedexStatusEnum.INITIALIZING,
                }
            )
            trainer.pokedex_status = PokedexStatusEnum.INITIALIZING

            await self.my_pokemon_service.capture(trainer.id, starter)

            await self.user_repository.update_status(user_id, StatusEnum.COMPLETE)

            if background_tasks is not None:
                background_tasks.add_task(
                    run_pokedex_initialization_task,
                    trainer.id,
                    starter.name,
                )
            else:
                await self.pokedex_service.initialize_for_trainer(trainer.id, starter.name)
                await self.trainer_repository.update_pokedex_status(
                    trainer.id,
                    PokedexStatusEnum.READY,
                )
                trainer.pokedex_status = PokedexStatusEnum.READY

            return InitializeTrainerResponse(
                id=trainer.id,
                user_id=trainer.user_id,
                pokeballs=trainer.pokeballs,
                capture_rate=trainer.capture_rate,
                pokedex_status=trainer.pokedex_status,
                pokemon_name=starter.name,
                created_at=trainer.created_at,
            )

        except Exception as exception:
            handle_service_exception(
                exception,
                logger=logger,
                service='TrainerService',
                operation='initialize',
                raise_exception=True,
            )
