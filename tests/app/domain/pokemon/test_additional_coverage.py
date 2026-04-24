from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.domain.pokemon.repository import PokemonRepository
from app.domain.pokemon.route import (
    get_poke_api_client,
    get_pokemon_ability_service,
    get_pokemon_growth_rate_service,
    get_pokemon_move_service,
    get_pokemon_service,
    get_pokemon_type_service,
    list_abilities,
    list_growth_rates,
    list_types,
)
from app.domain.pokemon.service import PokemonService, _pick_sprite_image
from app.domain.pokemon_ability.repository import PokemonAbilityRepository
from app.domain.pokemon_ability.service import PokemonAbilityService
from app.domain.pokemon_growth_rate.repository import PokemonGrowthRateRepository
from app.domain.pokemon_growth_rate.service import PokemonGrowthRateService
from app.domain.pokemon_move.repository import PokemonMoveRepository
from app.domain.pokemon_move.service import PokemonMoveService
from app.domain.pokemon_type.repository import PokemonTypeRepository
from app.domain.pokemon_type.service import PokemonTypeService
from app.models.enums import StatusEnum
from app.models.pokemon import Pokemon
from app.models.pokemon_ability import PokemonAbility
from app.models.pokemon_growth_rate import PokemonGrowthRate
from app.models.pokemon_move import PokemonMove
from app.infrastructure.external_api.schemas import PokemonExternalBaseSpritesSchemaResponse


class TestPokemonRouteProviders:
    def test_route_service_factories_build_expected_services(self):
        session = AsyncMock()
        pokeapi_client = get_poke_api_client()

        assert isinstance(get_pokemon_service(session, pokeapi_client), PokemonService)
        assert isinstance(get_pokemon_move_service(session), PokemonMoveService)
        assert isinstance(get_pokemon_ability_service(session), PokemonAbilityService)
        assert isinstance(get_pokemon_type_service(session), PokemonTypeService)
        assert isinstance(get_pokemon_growth_rate_service(session), PokemonGrowthRateService)

    @staticmethod
    @pytest.mark.asyncio
    async def test_related_resource_routes_delegate_to_services():
        user = {'id': '1'}
        service = AsyncMock()
        service.list_all = AsyncMock(return_value=['ok'])

        assert await list_abilities(_=user, service=service) == ['ok']
        assert await list_types(_=user, service=service) == ['ok']
        assert await list_growth_rates(_=user, service=service) == ['ok']


class TestPokemonServiceAdditionalBranches:
    @staticmethod
    def test_pick_sprite_image_returns_none_when_all_sprites_are_empty():
        sprites = PokemonExternalBaseSpritesSchemaResponse(
            front_default=None,
            front_shiny=None,
            front_female=None,
            back_default=None,
        )

        assert _pick_sprite_image(sprites) is None

    @staticmethod
    @pytest.mark.asyncio
    async def test_complete_pokemon_re_raises_http_exception():
        service = PokemonService(
            repository=AsyncMock(),
            move_repository=AsyncMock(),
            ability_repository=AsyncMock(),
            type_repository=AsyncMock(),
            growth_rate_repository=AsyncMock(),
            pokeapi_client=AsyncMock(),
        )
        service.repository.find_by = AsyncMock(return_value=SimpleNamespace(name='pikachu'))
        service.pokeapi_client.get_pokemon = AsyncMock(
            side_effect=__import__('fastapi').HTTPException(status_code=400, detail='bad request')
        )

        with pytest.raises(Exception) as exc_info:
            await service.complete_pokemon('pikachu')

        assert exc_info.value.status_code == 400

    @staticmethod
    @pytest.mark.asyncio
    async def test_complete_pokemon_adds_evolutions_when_chain_is_present():
        service = PokemonService(
            repository=AsyncMock(),
            move_repository=AsyncMock(),
            ability_repository=AsyncMock(),
            type_repository=AsyncMock(),
            growth_rate_repository=AsyncMock(),
            pokeapi_client=AsyncMock(),
        )
        pokemon = SimpleNamespace(name='pikachu', evolution_chain=None)
        service.repository.find_by = AsyncMock(return_value=pokemon)
        service.repository.update = AsyncMock(return_value=pokemon)
        service.add_moves = AsyncMock(return_value=[])
        service.add_abilities = AsyncMock(return_value=[])
        service.add_types = AsyncMock(return_value=[])
        service.add_growth_rate = AsyncMock(return_value=None)
        service.add_evolutions = AsyncMock(return_value=['raichu'])
        service.pokeapi_client.get_pokemon = AsyncMock(
            return_value=SimpleNamespace(
                stats=[],
                sprites=SimpleNamespace(front_default=None, front_shiny=None, front_female=None, back_default=None),
                height=4,
                weight=60,
                base_experience=112,
                moves=[],
                abilities=[],
                types=[],
            )
        )
        service.pokeapi_client.get_pokemon_species = AsyncMock(
            return_value=SimpleNamespace(
                habitat=None,
                is_baby=False,
                shape=None,
                is_mythical=False,
                gender_rate=4,
                is_legendary=False,
                capture_rate=190,
                hatch_counter=10,
                base_happiness=50,
                evolution_chain=SimpleNamespace(url='/evolution-chain/10'),
                evolves_from_species=None,
                has_gender_differences=False,
                growth_rate=None,
            )
        )

        await service.complete_pokemon('pikachu', with_evolutions=True)

        assert pokemon.evolutions == ['raichu']

    @staticmethod
    @pytest.mark.asyncio
    async def test_add_types_reuses_existing_types():
        service = PokemonService(
            repository=AsyncMock(),
            move_repository=AsyncMock(),
            ability_repository=AsyncMock(),
            type_repository=AsyncMock(),
            growth_rate_repository=AsyncMock(),
            pokeapi_client=AsyncMock(),
        )
        existing = SimpleNamespace(name='electric')
        service.type_repository.find_by = AsyncMock(return_value=existing)

        result = await service.add_types(
            [SimpleNamespace(type=SimpleNamespace(name='electric', url='/type/13'))]
        )

        assert result == [existing]


class TestPokemonRepositoriesServicesAndModels:
    @staticmethod
    @pytest.mark.asyncio
    async def test_small_repositories_delegate_create_to_save():
        move_repository = PokemonMoveRepository(session=AsyncMock())
        move_repository.save = AsyncMock(return_value='move')
        ability_repository = PokemonAbilityRepository(session=AsyncMock())
        ability_repository.save = AsyncMock(return_value='ability')
        type_repository = PokemonTypeRepository(session=AsyncMock())
        type_repository.save = AsyncMock(return_value='type')
        growth_rate_repository = PokemonGrowthRateRepository(session=AsyncMock())
        growth_rate_repository.save = AsyncMock(return_value='growth-rate')
        pokemon_repository = PokemonRepository(session=AsyncMock())
        pokemon_repository.save = AsyncMock(return_value='pokemon')

        assert await move_repository.create({
            'pp': 15, 'url': '/move/9', 'type': 'electric', 'name': 'thunder-punch',
            'order': 9, 'power': 75, 'target': 'selected-pokemon', 'effect': 'Hit',
            'priority': 0, 'accuracy': 100, 'short_effect': 'Hit', 'damage_class': 'physical',
            'effect_chance': None,
        }) == 'move'
        assert await ability_repository.create({'url': '/ability/9', 'order': 1, 'name': 'static', 'slot': 1, 'is_hidden': False}) == 'ability'
        assert await type_repository.create({'url': '/type/13', 'order': 13, 'name': 'electric'}) == 'type'
        assert await growth_rate_repository.create({'url': '/growth-rate/2', 'name': 'medium-fast', 'formula': 'x^3', 'description': 'Medium fast'}) == 'growth-rate'
        assert await pokemon_repository.create({'name': 'pikachu', 'order': 25, 'external_image': 'https://image/pikachu.png', 'status': StatusEnum.INCOMPLETE}) == 'pokemon'

    def test_small_services_can_be_constructed(self):
        assert isinstance(PokemonMoveService(AsyncMock()), PokemonMoveService)
        assert isinstance(PokemonAbilityService(AsyncMock()), PokemonAbilityService)
        assert isinstance(PokemonTypeService(AsyncMock()), PokemonTypeService)
        assert isinstance(PokemonGrowthRateService(AsyncMock()), PokemonGrowthRateService)

    def test_model_default_timestamps_are_initialized(self):
        pokemon = Pokemon(name='pikachu', order=25, external_image='https://image/pikachu.png', status=StatusEnum.INCOMPLETE)
        ability = PokemonAbility(url='/ability/9', order=1, name='static', slot=1, is_hidden=False)
        growth_rate = PokemonGrowthRate(url='/growth-rate/2', name='medium-fast', formula='x^3', description='Medium fast')
        move = PokemonMove(
            pp=15, url='/move/9', type='electric', name='thunder-punch', order=9, power=75,
            target='selected-pokemon', effect='Hit', priority=0, accuracy=100, short_effect='Hit',
            damage_class='physical', effect_chance=None,
        )

        assert pokemon.created_at is not None
        assert ability.created_at is not None
        assert growth_rate.created_at is not None
        assert move.created_at is not None
