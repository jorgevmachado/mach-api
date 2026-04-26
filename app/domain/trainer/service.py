from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from app.core.exceptions import handle_service_exception
from app.domain.auth.repository import UserRepository
from app.domain.my_pokemon.service import MyPokemonService
from app.domain.pokedex.service import PokedexService
from app.domain.pokemon.service import PokemonService
from app.domain.trainer.repository import TrainerRepository
from app.domain.trainer.schema import (
    TrainerInitializeResultSchema,
    TrainerInitializeSchema,
    TrainerMeSchema,
)
from app.models.enums import PokedexStatusEnum, StatusEnum
from app.models.user import User

logger = logging.getLogger(__name__)
INITIALIZATION_STALE_AFTER = timedelta(minutes=2)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


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
        data: TrainerInitializeSchema,
    ) -> TrainerInitializeResultSchema:
        try:
            existing = await self.trainer_repository.get_by_user_id(user_id)
            if existing:
                return await self._initialize_existing_trainer(existing, data)

            starter = await self._resolve_starter(data.pokemon_name)
            trainer = await self.trainer_repository.create(
                {
                    'user_id': user_id,
                    'pokeballs': data.pokeballs,
                    'capture_rate': data.capture_rate,
                    'pokedex_status': PokedexStatusEnum.INITIALIZING,
                }
            )
            trainer_id = trainer.id
            trainer_user_id = trainer.user_id
            trainer_pokeballs = trainer.pokeballs
            trainer_capture_rate = trainer.capture_rate
            trainer_created_at = trainer.created_at
            trainer.pokedex_status = PokedexStatusEnum.INITIALIZING

            try:
                await self.my_pokemon_service.capture(trainer_id, starter)
                await self.pokedex_service.initialize_for_trainer(trainer_id, starter.name)
                await self.user_repository.update_status(user_id, StatusEnum.COMPLETE)
                await self.trainer_repository.update_pokedex_status(
                    trainer_id,
                    PokedexStatusEnum.READY,
                )
            except Exception:
                await self.trainer_repository.update_pokedex_status(
                    trainer_id,
                    PokedexStatusEnum.FAILED,
                )
                raise

            trainer.pokedex_status = PokedexStatusEnum.READY

            return TrainerInitializeResultSchema(
                id=trainer_id,
                user_id=trainer_user_id,
                pokeballs=trainer_pokeballs,
                capture_rate=trainer_capture_rate,
                pokedex_status=trainer.pokedex_status,
                pokemon_name=starter.name,
                message='Trainer initialized successfully.',
                created_at=trainer_created_at,
            )

        except Exception as exception:
            handle_service_exception(
                exception,
                logger=logger,
                service='TrainerService',
                operation='initialize',
                raise_exception=True,
            )

    async def get_me(self, current_user: User) -> TrainerMeSchema:
        trainer = await self.trainer_repository.get_by_user_id(current_user.id)
        if trainer is None:
            return TrainerMeSchema(
                id=UUID('00000000-0000-0000-0000-000000000000'),
                user_id=current_user.id,
                pokeballs=0,
                capture_rate=0,
                pokedex_status=PokedexStatusEnum.EMPTY,
                created_at=current_user.created_at,
            )
        return TrainerMeSchema.model_validate(trainer)

    async def _initialize_existing_trainer(
        self,
        trainer,
        data: TrainerInitializeSchema,
    ) -> TrainerInitializeResultSchema:
        trainer_id = trainer.id
        trainer_user_id = trainer.user_id
        trainer_pokeballs = trainer.pokeballs
        trainer_capture_rate = trainer.capture_rate
        trainer_created_at = trainer.created_at
        starter_entry = next(iter(trainer.my_pokemons), None)
        starter_name = starter_entry.pokemon.name if starter_entry is not None else None

        if trainer.pokedex_status == PokedexStatusEnum.INITIALIZING:
            if not self._is_initialization_stale(trainer):
                return TrainerInitializeResultSchema(
                    id=trainer_id,
                    user_id=trainer_user_id,
                    pokeballs=trainer_pokeballs,
                    capture_rate=trainer_capture_rate,
                    pokedex_status=trainer.pokedex_status,
                    pokemon_name=starter_name,
                    message='Trainer initialization is already in progress.',
                    created_at=trainer_created_at,
                )

            logger.warning(
                'Detected stale trainer initialization; retrying bootstrap',
                extra={
                    'service': 'TrainerService',
                    'operation': 'initialize',
                    'trainer_id': str(trainer_id),
                    'user_id': str(trainer_user_id),
                },
            )

        if trainer.pokedex_status in (
            PokedexStatusEnum.EMPTY,
            PokedexStatusEnum.FAILED,
            PokedexStatusEnum.INITIALIZING,
        ):
            if trainer.pokedex_status == PokedexStatusEnum.FAILED:
                return TrainerInitializeResultSchema(
                    id=trainer_id,
                    user_id=trainer_user_id,
                    pokeballs=trainer_pokeballs,
                    capture_rate=trainer_capture_rate,
                    pokedex_status=trainer.pokedex_status,
                    pokemon_name=starter_name,
                    message='A previous Pokedex initialization failed. Review the error before retrying.',
                    created_at=trainer_created_at,
                )

            starter = None
            if starter_name is None:
                starter = await self._resolve_starter(data.pokemon_name)
                await self.my_pokemon_service.capture(trainer_id, starter)
                starter_name = starter.name

            await self.trainer_repository.update_pokedex_status(
                trainer_id,
                PokedexStatusEnum.INITIALIZING,
            )
            trainer.pokedex_status = PokedexStatusEnum.INITIALIZING

            try:
                await self.pokedex_service.initialize_for_trainer(trainer_id, starter_name)
                await self.user_repository.update_status(trainer_user_id, StatusEnum.COMPLETE)
                await self.trainer_repository.update_pokedex_status(
                    trainer_id,
                    PokedexStatusEnum.READY,
                )
                trainer.pokedex_status = PokedexStatusEnum.READY
            except Exception:
                await self.trainer_repository.update_pokedex_status(
                    trainer_id,
                    PokedexStatusEnum.FAILED,
                )
                trainer.pokedex_status = PokedexStatusEnum.FAILED
                raise

        return TrainerInitializeResultSchema(
            id=trainer_id,
            user_id=trainer_user_id,
            pokeballs=trainer_pokeballs,
            capture_rate=trainer_capture_rate,
            pokedex_status=trainer.pokedex_status,
            pokemon_name=starter_name,
            message=None,
            created_at=trainer_created_at,
        )

    def _is_initialization_stale(self, trainer) -> bool:
        reference_at = trainer.updated_at or trainer.created_at
        if reference_at is None:
            return True
        return _utcnow() - reference_at >= INITIALIZATION_STALE_AFTER
