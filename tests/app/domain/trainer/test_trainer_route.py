from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.domain.trainer.route import get_trainer_service, initialize_trainer, me_trainer
from app.domain.trainer.schema import TrainerInitializeSchema
from app.domain.trainer.service import TrainerService
from app.models.enums import PokedexStatusEnum


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
            TrainerInitializeSchema(pokeballs=5, capture_rate=45),
            current_user=user,
            service=service,
        )

        assert result is trainer
        service.initialize.assert_awaited_once_with(
            user.id,
            TrainerInitializeSchema(pokeballs=5, capture_rate=45),
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_me_trainer_route_delegates_to_service():
        current_user = SimpleNamespace(id=uuid4(), created_at=datetime.now(timezone.utc))
        expected = SimpleNamespace(
            id=uuid4(),
            user_id=current_user.id,
            pokeballs=0,
            capture_rate=0,
            pokedex_status=PokedexStatusEnum.EMPTY,
        )
        service = AsyncMock()
        service.get_me.return_value = expected

        result = await me_trainer(current_user=current_user, service=service)

        assert result is expected
        service.get_me.assert_awaited_once_with(current_user)
