from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.my_pokemon.schema import MyPokemonUpdateSchema
from app.domain.my_pokemon.service import MyPokemonService


def build_my_pokemon_service(
    repository: AsyncMock | None = None,
) -> tuple[MyPokemonService, AsyncMock, AsyncMock]:
    repository = repository or AsyncMock()
    pokedex_service = AsyncMock()
    service = MyPokemonService(
        repository=repository,
        pokedex_service=pokedex_service,
    )
    return service, repository, pokedex_service


class TestMyPokemonSchema:
    def test_update_schema_rejects_short_nickname(self):
        with pytest.raises(ValidationError):
            MyPokemonUpdateSchema(nickname='ab')


class TestMyPokemonService:
    @staticmethod
    @pytest.mark.asyncio
    async def test_capture_discovers_species_after_creation():
        service, repository, pokedex_service = build_my_pokemon_service()
        captured = SimpleNamespace(
            id=uuid4(),
            nickname='Pikachu',
            updated_at=None,
        )
        repository.create.return_value = captured
        repository.update.return_value = SimpleNamespace(
            id=uuid4(),
            nickname='Pikachu',
            hp=30,
            iv_hp=0,
            ev_hp=0,
            wins=0,
            level=1,
            losses=0,
            max_hp=30,
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
            captured_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
            moves=[],
        )
        pokemon = SimpleNamespace(
            id=uuid4(),
            name='pikachu',
            hp=35,
            speed=90,
            attack=55,
            defense=30,
            special_attack=50,
            special_defense=50,
            growth_rate=SimpleNamespace(formula='medium'),
            moves=[],
        )

        await service.capture(uuid4(), pokemon)

        pokedex_service.discover.assert_awaited_once_with(
            repository.create.await_args.args[0]['trainer_id'],
            pokemon.id,
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_update_trainer_changes_nickname():
        service, repository, _ = build_my_pokemon_service()
        entry = SimpleNamespace(
            nickname='Old',
            hp=30,
            iv_hp=0,
            ev_hp=0,
            wins=0,
            level=1,
            losses=0,
            max_hp=30,
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
            id=uuid4(),
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
            captured_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
        )
        repository.find_by.return_value = entry
        repository.update.return_value = entry

        result = await service.update_trainer(
            str(uuid4()),
            uuid4(),
            MyPokemonUpdateSchema(nickname='Sparky'),
        )

        assert result.nickname == 'Sparky'

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_trainer_returns_detail_with_type_relations_loaded():
        service, repository, _ = build_my_pokemon_service()
        entry = SimpleNamespace(
            id=uuid4(),
            hp=30,
            iv_hp=0,
            ev_hp=0,
            wins=0,
            level=1,
            losses=0,
            max_hp=30,
            battles=0,
            nickname='Sparky',
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
            trainer_id=uuid4(),
            pokemon_id=uuid4(),
            captured_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
            moves=[],
            pokemon=SimpleNamespace(
                id=uuid4(),
                name='pikachu',
                order=25,
                status='COMPLETE',
                external_image='image',
                image=None,
                hp=35,
                speed=90,
                height=4,
                weight=60,
                attack=55,
                defense=30,
                habitat='forest',
                is_baby=False,
                shape_url=None,
                shape_name=None,
                is_mythical=False,
                gender_rate=4,
                is_legendary=False,
                capture_rate=190,
                hatch_counter=10,
                base_happiness=70,
                special_attack=50,
                base_experience=112,
                special_defense=50,
                evolution_chain=None,
                evolves_from_species=None,
                has_gender_differences=False,
                growth_rate=SimpleNamespace(
                    id=uuid4(),
                    name='medium',
                    url='url',
                    description='medium growth',
                    formula='medium',
                    created_at=datetime.now(timezone.utc),
                    updated_at=None,
                    deleted_at=None,
                ),
                moves=[],
                abilities=[],
                evolutions=[],
                types=[
                    SimpleNamespace(
                        id=uuid4(),
                        name='electric',
                        text_color='#000',
                        background_color='#fff',
                        url='url',
                        order=1,
                        weaknesses=[],
                        strengths=[],
                        created_at=datetime.now(timezone.utc),
                        updated_at=None,
                        deleted_at=None,
                    )
                ],
                created_at=datetime.now(timezone.utc),
                updated_at=None,
                deleted_at=None,
            ),
        )
        repository.find_by.return_value = entry

        result = await service.get_trainer(str(uuid4()), uuid4())

        assert result.pokemon.types[0].weaknesses == []
        assert result.pokemon.types[0].strengths == []
