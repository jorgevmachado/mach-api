from __future__ import annotations

from http import HTTPStatus
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.domain.pokemon.service import (
    PokemonService,
    _extract_stat,
    _flatten_evolutions,
    _pick_sprite_image,
)
from app.infrastructure.external_api.schemas import (
    NamedApiResourceSchema,
    PokemonExternalBaseAbilitySchemaResponse,
    PokemonExternalBaseMoveSchemaResponse,
    PokemonExternalBaseSchema,
    PokemonExternalBaseSpritesSchemaResponse,
    PokemonExternalBaseStatSchemaResponse,
    PokemonExternalBaseTypeSchemaResponse,
    PokemonExternalEvolutionChainLinkSchema,
)
from app.models.enums import StatusEnum
from app.models.pokemon_type import PokemonType, resolve_type_colors


def build_service() -> tuple[PokemonService, AsyncMock, AsyncMock]:
    repository = AsyncMock()
    move_repository = AsyncMock()
    ability_repository = AsyncMock()
    type_repository = AsyncMock()
    growth_rate_repository = AsyncMock()
    pokeapi_client = AsyncMock()

    service = PokemonService(
        repository=repository,
        move_repository=move_repository,
        ability_repository=ability_repository,
        type_repository=type_repository,
        growth_rate_repository=growth_rate_repository,
        pokeapi_client=pokeapi_client,
    )
    return service, repository, pokeapi_client


class TestPokemonServiceInitializeList:
    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_list_creates_catalog_when_total_is_zero():
        service, repository, pokeapi_client = build_service()
        repository.list_all = AsyncMock(return_value=['pikachu'])

        pokeapi_client.list_pokemon.return_value = [
            PokemonExternalBaseSchema(
                url='https://pokeapi.co/api/v2/pokemon/25/',
                order=25,
                name='pikachu',
                external_image='https://image/pikachu.png',
            )
        ]

        await service.initialize_list(total=0, external_total=1)

        repository.create.assert_awaited_once_with(
            {
                'name': 'pikachu',
                'order': 25,
                'status': StatusEnum.INCOMPLETE,
                'external_image': 'https://www.pokemon.com/static-assets/content-assets/cms2/img/pokedex/detail/025.png',
            }
        )
        repository.list_all.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_initialize_list_only_adds_missing_entries():
        service, repository, pokeapi_client = build_service()
        repository.find_by = AsyncMock(side_effect=[object(), None])
        repository.list_all = AsyncMock(return_value=['pikachu', 'bulbasaur'])

        pokeapi_client.list_pokemon.return_value = [
            PokemonExternalBaseSchema(
                url='https://pokeapi.co/api/v2/pokemon/25/',
                order=25,
                name='pikachu',
                external_image='https://image/pikachu.png',
            ),
            PokemonExternalBaseSchema(
                url='https://pokeapi.co/api/v2/pokemon/1/',
                order=1,
                name='bulbasaur',
                external_image='https://image/bulbasaur.png',
            ),
        ]

        await service.initialize_list(total=1, external_total=2)

        repository.create.assert_awaited_once_with(
            {
                'name': 'bulbasaur',
                'order': 1,
                'status': StatusEnum.INCOMPLETE,
                'external_image': 'https://www.pokemon.com/static-assets/content-assets/cms2/img/pokedex/detail/001.png',
            }
        )


class TestPokemonServiceGet:
    @staticmethod
    @pytest.mark.asyncio
    async def test_get_completes_incomplete_pokemon():
        service, _, _ = build_service()
        pokemon = SimpleNamespace(name='pikachu', status=StatusEnum.INCOMPLETE)
        completed = SimpleNamespace(name='pikachu', status=StatusEnum.COMPLETE)
        service.find_one = AsyncMock(return_value=pokemon)
        service.complete_pokemon = AsyncMock(return_value=completed)

        result = await service.get('pikachu')

        assert result is completed
        service.complete_pokemon.assert_awaited_once_with('pikachu')

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_returns_complete_pokemon_without_rehydration():
        service, _, _ = build_service()
        pokemon = SimpleNamespace(name='pikachu', status=StatusEnum.COMPLETE)
        service.find_one = AsyncMock(return_value=pokemon)
        service.complete_pokemon = AsyncMock()

        result = await service.get('pikachu')

        assert result is pokemon
        service.complete_pokemon.assert_not_awaited()


class TestPokemonServiceListCached:
    @staticmethod
    @pytest.mark.asyncio
    async def test_list_cached_uses_cache_before_fetching():
        service, _, _ = build_service()
        cached = ['cached-item']
        service.list_cache_service.build_key_list = AsyncMock(return_value='pokemon:list')
        service.list_cache_service.get_list = AsyncMock(return_value=cached)
        service.list = AsyncMock()

        result = await service.list_cached()

        assert result == cached
        service.list.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_cached_fetches_and_caches_on_miss():
        service, _, _ = build_service()
        service.list_cache_service.build_key_list = Mock(return_value='pokemon:list')
        service.list_cache_service.get_list = AsyncMock(return_value=None)
        service.list_cache_service.set_list = AsyncMock()
        service.list = AsyncMock(return_value=['fresh'])

        result = await service.list_cached()

        assert result == ['fresh']
        service.list_cache_service.set_list.assert_awaited_once_with('pokemon:list', ['fresh'])


class TestPokemonServiceHelpers:
    def test_pick_sprite_image_returns_first_available(self):
        sprites = PokemonExternalBaseSpritesSchemaResponse(
            front_default=None,
            front_shiny='https://image/shiny.png',
            front_female=None,
            back_default=None,
        )

        assert _pick_sprite_image(sprites) == 'https://image/shiny.png'

    def test_extract_stat_returns_matching_value_or_zero(self):
        stats = [
            PokemonExternalBaseStatSchemaResponse(
                stat=NamedApiResourceSchema(name='hp', url='/stat/1'),
                base_stat=35,
            )
        ]

        assert _extract_stat(stats, 'hp') == 35
        assert _extract_stat(stats, 'attack') == 0

    def test_flatten_evolutions_walks_recursively(self):
        chain = PokemonExternalEvolutionChainLinkSchema(
            species=NamedApiResourceSchema(name='pichu', url='/pokemon-species/172'),
            evolves_to=[
                PokemonExternalEvolutionChainLinkSchema(
                    species=NamedApiResourceSchema(name='pikachu', url='/pokemon-species/25'),
                    evolves_to=[
                        PokemonExternalEvolutionChainLinkSchema(
                            species=NamedApiResourceSchema(name='raichu', url='/pokemon-species/26'),
                            evolves_to=[],
                        )
                    ],
                )
            ],
        )

        assert _flatten_evolutions(chain) == ['pichu', 'pikachu', 'raichu']


class TestPokemonServiceSynchronization:
    @staticmethod
    @pytest.mark.asyncio
    async def test_total_delegates_to_repository():
        service, repository, _ = build_service()
        repository.total = AsyncMock(return_value=25)

        assert await service.total() == 25

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_sync_returns_false_when_meta_is_cached():
        service, _, _ = build_service()
        service.meta_cache.get_cache = AsyncMock(return_value={'total': 1})

        assert await service.list_sync() is False

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_sync_initializes_empty_catalog():
        service, _, pokeapi_client = build_service()
        service.meta_cache.get_cache = AsyncMock(return_value=None)
        service.meta_cache.set_cache = AsyncMock()
        service.total = AsyncMock(return_value=0)
        pokeapi_client.total = AsyncMock(return_value=2)
        service.initialize_list = AsyncMock()

        result = await service.list_sync()

        assert result is True
        service.initialize_list.assert_awaited_once_with(total=0, external_total=2)

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_sync_adds_missing_entries_when_external_total_is_higher():
        service, _, pokeapi_client = build_service()
        service.meta_cache.get_cache = AsyncMock(return_value=None)
        service.meta_cache.set_cache = AsyncMock()
        service.total = AsyncMock(side_effect=[1, 2])
        pokeapi_client.total = AsyncMock(return_value=2)
        service.initialize_list = AsyncMock()

        result = await service.list_sync()

        assert result is True
        service.initialize_list.assert_awaited_once_with(total=1, external_total=2)
        assert service.meta_cache.set_cache.await_count == 2

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_sync_returns_false_when_catalog_is_up_to_date():
        service, _, pokeapi_client = build_service()
        service.meta_cache.get_cache = AsyncMock(return_value=None)
        service.meta_cache.set_cache = AsyncMock()
        service.total = AsyncMock(return_value=2)
        pokeapi_client.total = AsyncMock(return_value=2)
        service.initialize_list = AsyncMock()

        assert await service.list_sync() is False
        service.initialize_list.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_uses_built_filter_and_repository():
        service, repository, _ = build_service()
        service.list_sync = AsyncMock()
        repository.list_all = AsyncMock(return_value=['pikachu'])

        result = await service.list()

        assert result == ['pikachu']
        repository.list_all.assert_awaited_once()

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_wraps_exceptions_as_http_errors():
        service, repository, _ = build_service()
        service.list_sync = AsyncMock()
        repository.list_all = AsyncMock(side_effect=RuntimeError('boom'))

        with pytest.raises(HTTPException) as exc_info:
            await service.list()

        assert exc_info.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestPokemonServiceCompletion:
    @staticmethod
    @pytest.mark.asyncio
    async def test_complete_pokemon_raises_when_not_found():
        service, repository, _ = build_service()
        repository.find_by = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await service.complete_pokemon('missing')

        assert exc_info.value.status_code == HTTPStatus.NOT_FOUND

    @staticmethod
    @pytest.mark.asyncio
    async def test_complete_pokemon_populates_details_without_evolutions():
        service, repository, pokeapi_client = build_service()
        pokemon = SimpleNamespace(
            name='pikachu',
            status=StatusEnum.INCOMPLETE,
            evolution_chain=None,
        )
        repository.find_by = AsyncMock(return_value=pokemon)
        repository.update = AsyncMock(return_value=pokemon)
        service.add_moves = AsyncMock(return_value=['move'])
        service.add_abilities = AsyncMock(return_value=['ability'])
        service.add_types = AsyncMock(return_value=['type'])
        service.add_growth_rate = AsyncMock(return_value='growth-rate')
        service.add_evolutions = AsyncMock()
        pokeapi_client.get_pokemon = AsyncMock(
            return_value=SimpleNamespace(
                stats=[
                    SimpleNamespace(stat=SimpleNamespace(name='hp'), base_stat=35),
                    SimpleNamespace(stat=SimpleNamespace(name='speed'), base_stat=90),
                    SimpleNamespace(stat=SimpleNamespace(name='attack'), base_stat=55),
                    SimpleNamespace(stat=SimpleNamespace(name='defense'), base_stat=40),
                    SimpleNamespace(stat=SimpleNamespace(name='special-attack'), base_stat=50),
                    SimpleNamespace(stat=SimpleNamespace(name='special-defense'), base_stat=50),
                ],
                sprites=SimpleNamespace(
                    front_default='https://image/pikachu.png',
                    front_shiny=None,
                    front_female=None,
                    back_default=None,
                ),
                height=4,
                weight=60,
                base_experience=112,
                moves=['move-ref'],
                abilities=['ability-ref'],
                types=['type-ref'],
            )
        )
        pokeapi_client.get_pokemon_species = AsyncMock(
            return_value=SimpleNamespace(
                habitat=SimpleNamespace(name='forest'),
                is_baby=False,
                shape=SimpleNamespace(name='quadruped', url='/shape/8'),
                is_mythical=False,
                gender_rate=4,
                is_legendary=False,
                capture_rate=190,
                hatch_counter=10,
                base_happiness=50,
                evolution_chain=SimpleNamespace(url=None),
                evolves_from_species=SimpleNamespace(name='pichu'),
                has_gender_differences=False,
                growth_rate=SimpleNamespace(name='medium-fast'),
            )
        )

        result = await service.complete_pokemon('pikachu', with_evolutions=False)

        assert result is pokemon
        assert pokemon.status == StatusEnum.COMPLETE
        assert pokemon.moves == ['move']
        assert pokemon.abilities == ['ability']
        assert pokemon.types == ['type']
        assert pokemon.growth_rate == 'growth-rate'
        service.add_evolutions.assert_not_awaited()

    @staticmethod
    @pytest.mark.asyncio
    async def test_complete_pokemon_wraps_unexpected_errors():
        service, repository, pokeapi_client = build_service()
        repository.find_by = AsyncMock(return_value=SimpleNamespace(name='pikachu'))
        pokeapi_client.get_pokemon = AsyncMock(side_effect=RuntimeError('boom'))

        with pytest.raises(HTTPException) as exc_info:
            await service.complete_pokemon('pikachu')

        assert exc_info.value.status_code == HTTPStatus.BAD_GATEWAY
        assert 'Failed to complete pokemon pikachu' in exc_info.value.detail


class TestPokemonServiceRelations:
    @staticmethod
    @pytest.mark.asyncio
    async def test_add_moves_reuses_existing_and_creates_new_moves():
        service, _, pokeapi_client = build_service()
        existing = SimpleNamespace(name='quick-attack')
        service.move_repository.find_by = AsyncMock(side_effect=[existing, None])
        created = SimpleNamespace(name='thunder-punch')
        service.move_repository.create = AsyncMock(return_value=created)
        pokeapi_client.get_move = AsyncMock(
            return_value=SimpleNamespace(
                pp=15,
                type=SimpleNamespace(name='electric'),
                name='thunder-punch',
                order=None,
                power=75,
                target=SimpleNamespace(name='selected-pokemon'),
                effect_entries=[
                    SimpleNamespace(
                        effect='Hit target',
                        short_effect='Hit',
                        language=SimpleNamespace(name='en'),
                    )
                ],
                damage_class=SimpleNamespace(name='physical'),
                effect_chance=None,
                accuracy=100,
                priority=0,
            )
        )

        result = await service.add_moves(
            [
                PokemonExternalBaseMoveSchemaResponse(
                    move=NamedApiResourceSchema(name='quick-attack', url='/move/98')
                ),
                PokemonExternalBaseMoveSchemaResponse(
                    move=NamedApiResourceSchema(name='thunder-punch', url='/move/9')
                ),
            ]
        )

        assert result == [existing, created]
        service.move_repository.create.assert_awaited_once_with(
            {
                'pp': 15,
                'url': '/move/9',
                'type': 'electric',
                'name': 'thunder-punch',
                'order': 9,
                'power': 75,
                'target': 'selected-pokemon',
                'effect': 'Hit target',
                'priority': 0,
                'accuracy': 100,
                'short_effect': 'Hit',
                'damage_class': 'physical',
                'effect_chance': None,
            }
        )

    @staticmethod
    @pytest.mark.asyncio
    async def test_add_abilities_reuses_existing_and_creates_new_abilities():
        service, _, _ = build_service()
        existing = SimpleNamespace(name='static')
        created = SimpleNamespace(name='lightning-rod')
        service.ability_repository.find_by = AsyncMock(side_effect=[existing, None])
        service.ability_repository.create = AsyncMock(return_value=created)

        result = await service.add_abilities(
            [
                PokemonExternalBaseAbilitySchemaResponse(
                    slot=1,
                    ability=NamedApiResourceSchema(name='static', url='/ability/9'),
                    is_hidden=False,
                ),
                PokemonExternalBaseAbilitySchemaResponse(
                    slot=3,
                    ability=NamedApiResourceSchema(name='lightning-rod', url='/ability/31'),
                    is_hidden=True,
                ),
            ]
        )

        assert result == [existing, created]

    @staticmethod
    @pytest.mark.asyncio
    async def test_add_types_creates_new_type_with_relations():
        service, _, pokeapi_client = build_service()
        created = PokemonType(url='/type/13', order=13, name='electric')
        related_ground = PokemonType(url='/type/5', order=5, name='ground')
        related_water = PokemonType(url='/type/11', order=11, name='water')
        service.type_repository.find_by = AsyncMock(return_value=None)
        service.type_repository.create = AsyncMock(return_value=created)
        service.type_repository.update = AsyncMock(return_value=created)
        pokeapi_client.get_type = AsyncMock(
            return_value=SimpleNamespace(
                id=13,
                damage_relations=SimpleNamespace(
                    double_damage_from=[SimpleNamespace(name='ground', url='/type/5')],
                    half_damage_from=[],
                    double_damage_to=[SimpleNamespace(name='water', url='/type/11')],
                    half_damage_to=[],
                ),
            )
        )
        service._resolve_type_relations = AsyncMock(side_effect=[[related_ground], [related_water]])

        result = await service.add_types(
            [
                PokemonExternalBaseTypeSchemaResponse(
                    type=NamedApiResourceSchema(name='electric', url='/type/13'),
                    slot=1,
                )
            ]
        )

        background_color, text_color = resolve_type_colors('electric')
        service.type_repository.create.assert_awaited_once_with(
            {
                'url': '/type/13',
                'order': 13,
                'name': 'electric',
                'text_color': text_color,
                'background_color': background_color,
            }
        )
        assert result == [created]
        assert created.weaknesses == [related_ground]
        assert created.strengths == [related_water]

    @staticmethod
    @pytest.mark.asyncio
    async def test_resolve_type_relations_reuses_or_creates_related_types():
        service, _, _ = build_service()
        existing = PokemonType(url='/type/5', order=5, name='ground')
        created = PokemonType(url='/type/11', order=11, name='water')
        service.type_repository.find_by = AsyncMock(side_effect=[existing, None])
        service.type_repository.create = AsyncMock(return_value=created)

        result = await service._resolve_type_relations(
            [
                SimpleNamespace(name='ground', url='https://pokeapi.co/api/v2/type/5/'),
                SimpleNamespace(name='water', url='https://pokeapi.co/api/v2/type/11/'),
            ]
        )

        assert result == [existing, created]

    @staticmethod
    @pytest.mark.asyncio
    async def test_add_growth_rate_handles_none_existing_and_new_resources():
        service, _, pokeapi_client = build_service()
        service.growth_rate_repository.find_by = AsyncMock(side_effect=[None, SimpleNamespace(name='fast')])
        service.growth_rate_repository.create = AsyncMock(return_value=SimpleNamespace(name='medium-fast'))
        pokeapi_client.get_growth_rate = AsyncMock(
            return_value=SimpleNamespace(
                name='medium-fast',
                formula='x^3',
                descriptions=[
                    SimpleNamespace(description='Medium fast', language=SimpleNamespace(name='en'))
                ],
            )
        )

        assert await service.add_growth_rate(None) is None
        created = await service.add_growth_rate(SimpleNamespace(name='medium-fast', url='/growth-rate/2'))
        existing = await service.add_growth_rate(SimpleNamespace(name='fast', url='/growth-rate/1'))

        assert created.name == 'medium-fast'
        assert existing.name == 'fast'

    @staticmethod
    @pytest.mark.asyncio
    async def test_add_evolutions_reuses_existing_and_creates_missing_entries():
        service, repository, pokeapi_client = build_service()
        existing = SimpleNamespace(name='raichu')
        created = SimpleNamespace(name='pichu')
        pokeapi_client.get_evolution_chain = AsyncMock(
            return_value=SimpleNamespace(
                chain=PokemonExternalEvolutionChainLinkSchema(
                    species=NamedApiResourceSchema(name='pichu', url='/pokemon-species/172'),
                    evolves_to=[
                        PokemonExternalEvolutionChainLinkSchema(
                            species=NamedApiResourceSchema(name='pikachu', url='/pokemon-species/25'),
                            evolves_to=[
                                PokemonExternalEvolutionChainLinkSchema(
                                    species=NamedApiResourceSchema(name='raichu', url='/pokemon-species/26'),
                                    evolves_to=[],
                                )
                            ],
                        )
                    ],
                )
            )
        )
        repository.find_by = AsyncMock(side_effect=[None, existing])
        repository.create = AsyncMock(return_value=created)
        pokeapi_client.get_pokemon = AsyncMock(
            return_value=SimpleNamespace(name='pichu', order=172)
        )

        result = await service.add_evolutions('/evolution-chain/10', 'pikachu')

        assert result == [created, existing]
