from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.trainer.repository import TrainerRepository
from app.domain.trainer.schema import TrainerInitializeSchema
from app.domain.trainer.service import TrainerService
from app.models.enums import PokedexStatusEnum, StatusEnum


class TestTrainerRepository:
    @staticmethod
    @pytest.mark.asyncio
    async def test_get_by_user_id_and_create():
        session = AsyncMock()
        repository = TrainerRepository(session=session)
        repository.save = AsyncMock(return_value=SimpleNamespace(id=uuid4()))

        await repository.get_by_user_id(uuid4())
        created = await repository.create(
            {'user_id': uuid4(), 'pokeballs': 5, 'capture_rate': 45}
        )

        session.scalar.assert_awaited_once()
        repository.save.assert_awaited_once()
        assert created is repository.save.await_args.args[0] or created is not None


class TestTrainerService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_existing_ready_trainer_returns_current_state():
        trainer_repository = AsyncMock()
        trainer_repository.get_by_user_id.return_value = SimpleNamespace(
            id=uuid4(),
            user_id=uuid4(),
            pokeballs=5,
            capture_rate=45,
            pokedex_status=PokedexStatusEnum.READY,
            created_at=datetime.now(timezone.utc),
            my_pokemons=[
                SimpleNamespace(
                    pokemon=SimpleNamespace(name='pikachu'),
                )
            ],
        )
        service = TrainerService(
            trainer_repository=trainer_repository,
            user_repository=AsyncMock(),
            pokemon_service=AsyncMock(),
            my_pokemon_service=AsyncMock(),
            pokedex_service=AsyncMock(),
        )

        result = await service.initialize(
            uuid4(),
            TrainerInitializeSchema(pokeballs=5, capture_rate=45),
        )

        assert result.pokemon_name == 'pikachu'
        assert result.pokedex_status == PokedexStatusEnum.READY

    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_existing_initializing_trainer_returns_message():
        trainer_repository = AsyncMock()
        trainer_repository.get_by_user_id.return_value = SimpleNamespace(
            id=uuid4(),
            user_id=uuid4(),
            pokeballs=5,
            capture_rate=45,
            pokedex_status=PokedexStatusEnum.INITIALIZING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            my_pokemons=[
                SimpleNamespace(
                    pokemon=SimpleNamespace(name='pikachu'),
                )
            ],
        )
        service = TrainerService(
            trainer_repository=trainer_repository,
            user_repository=AsyncMock(),
            pokemon_service=AsyncMock(),
            my_pokemon_service=AsyncMock(),
            pokedex_service=AsyncMock(),
        )

        result = await service.initialize(
            uuid4(),
            TrainerInitializeSchema(pokeballs=5, capture_rate=45),
        )

        assert result.pokedex_status == PokedexStatusEnum.INITIALIZING
        assert result.message == 'Trainer initialization is already in progress.'

    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_stale_initializing_trainer_retries_and_returns_ready():
        trainer_id = uuid4()
        user_id = uuid4()
        trainer_repository = AsyncMock()
        trainer_repository.get_by_user_id.return_value = SimpleNamespace(
            id=trainer_id,
            user_id=user_id,
            pokeballs=5,
            capture_rate=45,
            pokedex_status=PokedexStatusEnum.INITIALIZING,
            created_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            updated_at=datetime.now(timezone.utc) - timedelta(minutes=3),
            my_pokemons=[
                SimpleNamespace(
                    pokemon=SimpleNamespace(name='pikachu'),
                )
            ],
        )
        service = TrainerService(
            trainer_repository=trainer_repository,
            user_repository=AsyncMock(),
            pokemon_service=AsyncMock(),
            my_pokemon_service=AsyncMock(),
            pokedex_service=AsyncMock(),
        )

        result = await service.initialize(
            user_id,
            TrainerInitializeSchema(pokeballs=5, capture_rate=45),
        )

        assert result.pokedex_status == PokedexStatusEnum.READY
        service.pokedex_service.initialize_for_trainer.assert_awaited_once_with(
            trainer_id,
            'pikachu',
        )
        assert trainer_repository.update_pokedex_status.await_args_list[0].args == (
            trainer_id,
            PokedexStatusEnum.INITIALIZING,
        )
        assert trainer_repository.update_pokedex_status.await_args_list[1].args == (
            trainer_id,
            PokedexStatusEnum.READY,
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_creates_trainer_and_returns_ready():
        trainer_repository = AsyncMock()
        trainer = SimpleNamespace(
            id=uuid4(),
            user_id=uuid4(),
            pokeballs=5,
            capture_rate=45,
            pokedex_status=PokedexStatusEnum.INITIALIZING,
            created_at=datetime.now(timezone.utc),
        )
        trainer_repository.get_by_user_id.return_value = None
        trainer_repository.create.return_value = trainer
        user_repository = AsyncMock()
        pokemon = SimpleNamespace(id=uuid4(), name='pikachu', status=StatusEnum.COMPLETE)
        pokemon_service = AsyncMock()
        pokemon_service.list_sync.return_value = True
        pokemon_service.get.return_value = pokemon
        pokemon_service.repository = SimpleNamespace(
            find_by=AsyncMock(return_value=pokemon),
            list_all=AsyncMock(return_value=[pokemon]),
        )
        my_pokemon_service = AsyncMock()
        pokedex_service = AsyncMock()
        user_id = uuid4()
        service = TrainerService(
            trainer_repository=trainer_repository,
            user_repository=user_repository,
            pokemon_service=pokemon_service,
            my_pokemon_service=my_pokemon_service,
            pokedex_service=pokedex_service,
        )
        service._resolve_starter = AsyncMock(return_value=pokemon)

        result = await service.initialize(
            user_id,
            TrainerInitializeSchema(pokeballs=5, capture_rate=45, pokemon_name='pikachu'),
        )

        assert result.pokemon_name == 'pikachu'
        assert result.pokedex_status == PokedexStatusEnum.READY
        user_repository.update_status.assert_awaited_once_with(user_id, StatusEnum.COMPLETE)
        my_pokemon_service.capture.assert_awaited_once_with(trainer.id, pokemon)
        pokedex_service.initialize_for_trainer.assert_awaited_once_with(trainer.id, pokemon.name)
        trainer_repository.update_pokedex_status.assert_awaited_once_with(
            trainer.id,
            PokedexStatusEnum.READY,
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_retries_empty_trainer_and_returns_ready():
        trainer_id = uuid4()
        user_id = uuid4()
        trainer_repository = AsyncMock()
        trainer_repository.get_by_user_id.return_value = SimpleNamespace(
            id=trainer_id,
            user_id=user_id,
            pokeballs=5,
            capture_rate=45,
            pokedex_status=PokedexStatusEnum.EMPTY,
            created_at=datetime.now(timezone.utc),
            my_pokemons=[
                SimpleNamespace(
                    pokemon=SimpleNamespace(name='pikachu'),
                )
            ],
        )
        service = TrainerService(
            trainer_repository=trainer_repository,
            user_repository=AsyncMock(),
            pokemon_service=AsyncMock(),
            my_pokemon_service=AsyncMock(),
            pokedex_service=AsyncMock(),
        )

        result = await service.initialize(
            user_id,
            TrainerInitializeSchema(pokeballs=5, capture_rate=45),
        )

        assert result.pokedex_status == PokedexStatusEnum.READY
        service.pokedex_service.initialize_for_trainer.assert_awaited_once_with(
            trainer_id,
            'pikachu',
        )
        assert trainer_repository.update_pokedex_status.await_args_list[0].args == (
            trainer_id,
            PokedexStatusEnum.INITIALIZING,
        )
        assert trainer_repository.update_pokedex_status.await_args_list[1].args == (
            trainer_id,
            PokedexStatusEnum.READY,
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_existing_failed_trainer_returns_failure_message():
        trainer_id = uuid4()
        user_id = uuid4()
        trainer_repository = AsyncMock()
        trainer_repository.get_by_user_id.return_value = SimpleNamespace(
            id=trainer_id,
            user_id=user_id,
            pokeballs=5,
            capture_rate=45,
            pokedex_status=PokedexStatusEnum.FAILED,
            created_at=datetime.now(timezone.utc),
            my_pokemons=[
                SimpleNamespace(
                    pokemon=SimpleNamespace(name='pikachu'),
                )
            ],
        )
        service = TrainerService(
            trainer_repository=trainer_repository,
            user_repository=AsyncMock(),
            pokemon_service=AsyncMock(),
            my_pokemon_service=AsyncMock(),
            pokedex_service=AsyncMock(),
        )

        result = await service.initialize(
            user_id,
            TrainerInitializeSchema(pokeballs=5, capture_rate=45),
        )

        assert result.pokedex_status == PokedexStatusEnum.FAILED
        assert result.message == (
            'A previous Pokedex initialization failed. Review the error before retrying.'
        )
        service.pokedex_service.initialize_for_trainer.assert_not_awaited()
        trainer_repository.update_pokedex_status.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_failed_retry_marks_status_failed_and_raises():
        trainer_id = uuid4()
        user_id = uuid4()
        trainer_repository = AsyncMock()
        trainer_repository.get_by_user_id.return_value = SimpleNamespace(
            id=trainer_id,
            user_id=user_id,
            pokeballs=5,
            capture_rate=45,
            pokedex_status=PokedexStatusEnum.EMPTY,
            created_at=datetime.now(timezone.utc),
            my_pokemons=[
                SimpleNamespace(
                    pokemon=SimpleNamespace(name='pikachu'),
                )
            ],
        )
        pokedex_service = AsyncMock()
        pokedex_service.initialize_for_trainer.side_effect = RuntimeError('boom')
        service = TrainerService(
            trainer_repository=trainer_repository,
            user_repository=AsyncMock(),
            pokemon_service=AsyncMock(),
            my_pokemon_service=AsyncMock(),
            pokedex_service=pokedex_service,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.initialize(
                user_id,
                TrainerInitializeSchema(pokeballs=5, capture_rate=45),
            )

        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert trainer_repository.update_pokedex_status.await_args_list[-1].args == (
            trainer_id,
            PokedexStatusEnum.FAILED,
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_me_returns_empty_trainer_schema_when_missing():
        current_user = SimpleNamespace(
            id=uuid4(),
            created_at=datetime.now(timezone.utc),
        )
        trainer_repository = AsyncMock()
        trainer_repository.get_by_user_id.return_value = None
        service = TrainerService(
            trainer_repository=trainer_repository,
            user_repository=AsyncMock(),
            pokemon_service=AsyncMock(),
            my_pokemon_service=AsyncMock(),
            pokedex_service=AsyncMock(),
        )

        result = await service.get_me(current_user)

        assert result.user_id == current_user.id
        assert result.pokedex_status == PokedexStatusEnum.EMPTY
