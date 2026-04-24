from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks
from fastapi import HTTPException
from pydantic import ValidationError

from app.domain.auth.repository import UserRepository
from app.domain.auth.route import get_auth_service, login, me, register
from app.domain.auth.schema import LoginRequest, RegisterRequest
from app.domain.auth.service import AuthService
from app.domain.trainer.repository import TrainerRepository
from app.domain.trainer.route import get_trainer_service, initialize_trainer
from app.domain.trainer.schema import InitializeTrainerRequest
from app.domain.trainer.service import TrainerService
from app.models.enums import GenderEnum, PokedexStatusEnum, StatusEnum


def build_register_request() -> RegisterRequest:
    return RegisterRequest(
        name='Ash Ketchum',
        email='ash@example.com',
        username='ash',
        gender=GenderEnum.MALE,
        date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
        password='pikachu123',
    )


class TestAuthSchema:
    def test_register_request_rejects_short_password(self):
        with pytest.raises(ValidationError):
            RegisterRequest(
                name='Ash',
                email='ash@example.com',
                username='ash',
                gender=GenderEnum.MALE,
                date_of_birth=datetime(1990, 1, 1, tzinfo=timezone.utc),
                password='short',
            )


class TestUserRepository:
    @staticmethod
    @pytest.mark.asyncio
    async def test_get_by_variants_delegate_to_scalar():
        session = AsyncMock()
        repository = UserRepository(session=session)

        await repository.get_by_email('ash@example.com')
        await repository.get_by_username('ash')
        await repository.get_by_email_or_username('ash')

        assert session.scalar.await_count == 3

    @staticmethod
    @pytest.mark.asyncio
    async def test_create_builds_user_and_delegates_to_save():
        session = AsyncMock()
        repository = UserRepository(session=session)
        expected = SimpleNamespace(id=uuid4())
        repository.save = AsyncMock(return_value=expected)

        result = await repository.create(build_register_request().model_dump() | {'status': StatusEnum.INCOMPLETE})

        assert result is expected
        repository.save.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_methods_execute_and_commit():
        session = AsyncMock()
        repository = UserRepository(session=session)
        user_id = uuid4()

        await repository.update_auth_success(user_id)
        await repository.update_auth_failure(user_id)
        await repository.update_status(user_id, StatusEnum.COMPLETE)
        await repository.soft_delete(user_id)

        assert session.execute.await_count == 4
        assert session.commit.await_count == 4


class TestAuthService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_register_rejects_existing_email():
        repository = AsyncMock()
        repository.get_by_email.return_value = object()
        service = AuthService(repository=repository)

        with pytest.raises(HTTPException) as exc_info:
            await service.register(build_register_request())

        assert exc_info.value.status_code == HTTPStatus.CONFLICT
        assert exc_info.value.detail == 'Email already registered'

    @staticmethod
    @pytest.mark.asyncio
    async def test_register_rejects_existing_username():
        repository = AsyncMock()
        repository.get_by_email.return_value = None
        repository.get_by_username.return_value = object()
        service = AuthService(repository=repository)

        with pytest.raises(HTTPException) as exc_info:
            await service.register(build_register_request())

        assert exc_info.value.status_code == HTTPStatus.CONFLICT
        assert exc_info.value.detail == 'Username already taken'

    @staticmethod
    @pytest.mark.asyncio
    async def test_register_creates_hashed_user(monkeypatch):
        repository = AsyncMock()
        repository.get_by_email.return_value = None
        repository.get_by_username.return_value = None
        created = SimpleNamespace(id=uuid4())
        repository.create.return_value = created
        monkeypatch.setattr('app.domain.auth.service.get_password_hash', lambda _: 'hashed-password')
        service = AuthService(repository=repository)

        result = await service.register(build_register_request())

        assert result is created
        repository.create.assert_awaited_once()
        payload = repository.create.await_args.args[0]
        assert payload['password'] == 'hashed-password'
        assert payload['status'] == StatusEnum.INCOMPLETE

    @staticmethod
    @pytest.mark.asyncio
    async def test_login_rejects_missing_user():
        repository = AsyncMock()
        repository.get_by_email_or_username.return_value = None
        service = AuthService(repository=repository)

        with pytest.raises(HTTPException) as exc_info:
            await service.login(LoginRequest(credential='ash', password='pikachu123'))

        assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
        assert exc_info.value.detail == 'Invalid credentials'

    @staticmethod
    @pytest.mark.asyncio
    async def test_login_rejects_invalid_password(monkeypatch):
        user = SimpleNamespace(id=uuid4(), password='hashed')
        repository = AsyncMock()
        repository.get_by_email_or_username.return_value = user
        monkeypatch.setattr('app.domain.auth.service.verify_password', lambda *_: False)
        service = AuthService(repository=repository)

        with pytest.raises(HTTPException) as exc_info:
            await service.login(LoginRequest(credential='ash', password='bad-password'))

        assert exc_info.value.status_code == HTTPStatus.UNAUTHORIZED
        repository.update_auth_failure.assert_awaited_once_with(user.id)

    @staticmethod
    @pytest.mark.asyncio
    async def test_login_returns_token_for_valid_user(monkeypatch):
        user = SimpleNamespace(id=uuid4(), password='hashed')
        repository = AsyncMock()
        repository.get_by_email_or_username.return_value = user
        monkeypatch.setattr('app.domain.auth.service.verify_password', lambda *_: True)
        monkeypatch.setattr('app.domain.auth.service.create_access_token', lambda payload: f"token-{payload['sub']}")
        service = AuthService(repository=repository)

        result = await service.login(LoginRequest(credential='ash', password='pikachu123'))

        assert result == {'access_token': f'token-{user.id}', 'token_type': 'bearer'}
        repository.update_auth_success.assert_awaited_once_with(user.id)


class TestAuthRoutes:
    @staticmethod
    def test_get_auth_service_builds_service():
        service = get_auth_service(AsyncMock())
        assert isinstance(service, AuthService)

    @staticmethod
    @pytest.mark.asyncio
    async def test_register_route_returns_service_result():
        service = AsyncMock()
        data = build_register_request()
        expected = SimpleNamespace(id=uuid4())
        service.register.return_value = expected

        result = await register(data, service=service)

        assert result is expected

    @staticmethod
    @pytest.mark.asyncio
    async def test_login_route_returns_token_payload():
        service = AsyncMock()
        service.login.return_value = {'access_token': 'token', 'token_type': 'bearer'}

        result = await login(LoginRequest(credential='ash', password='pikachu123'), service=service)

        assert result['access_token'] == 'token'

    @staticmethod
    @pytest.mark.asyncio
    async def test_me_route_returns_current_user():
        user = SimpleNamespace(id=uuid4())
        assert await me(current_user=user) is user


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
    async def test_initialize_existing_trainer_returns_current_state():
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
        user_repository = AsyncMock()
        pokemon_service = AsyncMock()
        my_pokemon_service = AsyncMock()
        pokedex_service = AsyncMock()
        service = TrainerService(
            trainer_repository=trainer_repository,
            user_repository=user_repository,
            pokemon_service=pokemon_service,
            my_pokemon_service=my_pokemon_service,
            pokedex_service=pokedex_service,
        )

        result = await service.initialize(uuid4(), InitializeTrainerRequest(pokeballs=5, capture_rate=45))

        assert result.pokemon_name == 'pikachu'
        assert result.pokedex_status == PokedexStatusEnum.READY

    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_creates_trainer_and_updates_status():
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
        pokemon_service.repository.list_all.return_value = [pokemon]
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

        result = await service.initialize(
            user_id,
            InitializeTrainerRequest(pokeballs=5, capture_rate=45),
            background_tasks=BackgroundTasks(),
        )

        assert result.pokemon_name == 'pikachu'
        user_repository.update_status.assert_awaited_once_with(user_id, StatusEnum.COMPLETE)
        my_pokemon_service.capture.assert_awaited_once_with(trainer.id, pokemon)


class TestTrainerRoutes:
    @staticmethod
    def test_get_trainer_service_builds_service():
        service = get_trainer_service(AsyncMock())
        assert isinstance(service, TrainerService)

    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_trainer_route_delegates_to_service():
        user = SimpleNamespace(id=uuid4())
        trainer = SimpleNamespace(id=uuid4(), pokemon_name='pikachu')
        service = AsyncMock()
        service.initialize.return_value = trainer

        result = await initialize_trainer(
            InitializeTrainerRequest(pokeballs=5, capture_rate=45),
            background_tasks=BackgroundTasks(),
            current_user=user,
            service=service,
        )

        assert result is trainer
        service.initialize.assert_awaited_once()
