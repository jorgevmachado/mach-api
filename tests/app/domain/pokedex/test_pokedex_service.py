from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.domain.pokedex.schema import PokedexUpdateSchema
from app.domain.pokedex.service import PokedexService


def build_pokedex_service(repository: AsyncMock | None = None) -> tuple[PokedexService, AsyncMock]:
    repository = repository or AsyncMock()
    service = PokedexService(
        repository=repository,
        pokemon_repository=AsyncMock(),
        trainer_repository=AsyncMock(),
    )
    return service, repository


class TestPokedexService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_get_trainer_rejects_undiscovered_entry():
        service, repository = build_pokedex_service()
        repository.find_by.return_value = SimpleNamespace(
            deleted_at=None,
            discovered=False,
        )

        with pytest.raises(HTTPException) as exc_info:
            await service.get_trainer(str(uuid4()), uuid4())

        assert exc_info.value.status_code == 403

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_trainer_sets_discovered_at_when_discovery_changes():
        service, repository = build_pokedex_service()
        entry = SimpleNamespace(
            id=uuid4(),
            discovered=False,
            deleted_at=None,
            hp=10,
            iv_hp=0,
            ev_hp=0,
            wins=0,
            level=1,
            losses=0,
            max_hp=10,
            battles=0,
            speed=10,
            iv_speed=0,
            ev_speed=0,
            attack=10,
            iv_attack=0,
            ev_attack=0,
            defense=10,
            iv_defense=0,
            ev_defense=0,
            experience=0,
            special_attack=10,
            iv_special_attack=0,
            ev_special_attack=0,
            special_defense=10,
            iv_special_defense=0,
            ev_special_defense=0,
            formula='test',
            pokemon=SimpleNamespace(
                id=uuid4(),
                name='pikachu',
                order=25,
                status='COMPLETE',
                external_image='image',
                image=None,
                types=[],
            ),
            trainer_id=uuid4(),
            pokemon_id=uuid4(),
            discovered_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=None,
        )
        repository.find_by.return_value = entry
        repository.update.return_value = entry

        result = await service.update_trainer(
          str(uuid4()),
          uuid4(),
          PokedexUpdateSchema(discovered=True),
        )

        assert result.discovered is True
        assert entry.discovered_at is not None
