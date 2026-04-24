from __future__ import annotations

from http import HTTPStatus
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import HTTPException

from app.infrastructure.external_api.pokeapi_client import PokeApiClient


class FakeResponse:
    def __init__(self, payload, status_code=200, is_success=True):
        self._payload = payload
        self.status_code = status_code
        self.is_success = is_success

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, response=None, error=None, **kwargs):
        self.response = response
        self.error = error
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url):
        if self.error:
            raise self.error
        return self.response


class TestPokeApiClientRequest:
    @staticmethod
    @pytest.mark.asyncio
    async def test_request_success(monkeypatch):
        captured = {}

        def fake_client(**kwargs):
            captured.update(kwargs)
            return FakeAsyncClient(response=FakeResponse({'ok': True}))

        monkeypatch.setattr('app.infrastructure.external_api.pokeapi_client.httpx.AsyncClient', fake_client)
        client = PokeApiClient(base_url='https://pokeapi.co/api/v2', verify_ssl=False)

        result = await client._request('pokemon')

        assert result == {'ok': True}
        assert captured['verify'] is False
        assert captured['trust_env'] is True

    @staticmethod
    @pytest.mark.asyncio
    async def test_request_wraps_ssl_error(monkeypatch):
        error = httpx.HTTPError('CERTIFICATE_VERIFY_FAILED')
        monkeypatch.setattr(
            'app.infrastructure.external_api.pokeapi_client.httpx.AsyncClient',
            lambda **kwargs: FakeAsyncClient(error=error),
        )
        client = PokeApiClient(base_url='https://pokeapi.co/api/v2')

        with pytest.raises(HTTPException) as exc_info:
            await client._request('pokemon')

        assert exc_info.value.status_code == HTTPStatus.BAD_GATEWAY
        assert 'POKEAPI_CA_BUNDLE' in exc_info.value.detail

    @staticmethod
    @pytest.mark.asyncio
    async def test_request_handles_not_found(monkeypatch):
        monkeypatch.setattr(
            'app.infrastructure.external_api.pokeapi_client.httpx.AsyncClient',
            lambda **kwargs: FakeAsyncClient(
                response=FakeResponse({}, status_code=HTTPStatus.NOT_FOUND, is_success=False)
            ),
        )
        client = PokeApiClient(base_url='https://pokeapi.co/api/v2')

        with pytest.raises(HTTPException) as exc_info:
            await client._request('pokemon/99999')

        assert exc_info.value.detail.endswith('pokemon/99999')

    @staticmethod
    @pytest.mark.asyncio
    async def test_request_handles_non_success(monkeypatch):
        monkeypatch.setattr(
            'app.infrastructure.external_api.pokeapi_client.httpx.AsyncClient',
            lambda **kwargs: FakeAsyncClient(
                response=FakeResponse({}, status_code=503, is_success=False)
            ),
        )
        client = PokeApiClient(base_url='https://pokeapi.co/api/v2')

        with pytest.raises(HTTPException) as exc_info:
            await client._request('pokemon')

        assert exc_info.value.detail == 'PokeAPI returned status 503 for https://pokeapi.co/api/v2/pokemon'


class TestPokeApiClientMethods:
    @staticmethod
    @pytest.mark.asyncio
    async def test_list_pokemon_maps_results():
        client = PokeApiClient(base_url='https://pokeapi.co/api/v2')
        client._request = AsyncMock(return_value={
            'count': 2,
            'results': [
                {'name': 'bulbasaur', 'url': 'https://pokeapi.co/api/v2/pokemon/1/'},
                {'name': 'pikachu', 'url': 'https://pokeapi.co/api/v2/pokemon/25/'},
            ],
        })

        result = await client.list_pokemon(offset=0, limit=2)

        assert [item.name for item in result] == ['bulbasaur', 'pikachu']
        assert result[1].external_image.endswith('/025.png')

    @staticmethod
    @pytest.mark.asyncio
    async def test_total_returns_count():
        client = PokeApiClient(base_url='https://pokeapi.co/api/v2')
        client._request = AsyncMock(return_value={'count': 1350, 'results': []})

        assert await client.total() == 1350

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_resource_methods_validate_payloads():
        client = PokeApiClient(base_url='https://pokeapi.co/api/v2')

        client._request = AsyncMock(side_effect=[
            {
                'name': 'pikachu',
                'order': 25,
                'types': [{'type': {'name': 'electric', 'url': '/type/13'}, 'slot': 1}],
                'moves': [{'move': {'name': 'thunder-punch', 'url': '/move/9'}}],
                'stats': [{'stat': {'name': 'hp', 'url': '/stat/1'}, 'base_stat': 35}],
                'height': 4,
                'weight': 60,
                'sprites': {'front_default': 'https://image/pikachu.png'},
                'abilities': [{'slot': 1, 'ability': {'name': 'static', 'url': '/ability/9'}, 'is_hidden': False}],
                'base_experience': 112,
            },
            {
                'name': 'pikachu',
                'shape': {'name': 'quadruped', 'url': '/shape/8'},
                'habitat': {'name': 'forest', 'url': '/habitat/3'},
                'is_baby': False,
                'growth_rate': {'name': 'medium-fast', 'url': '/growth-rate/2'},
                'gender_rate': 4,
                'is_mythical': False,
                'capture_rate': 190,
                'is_legendary': False,
                'hatch_counter': 10,
                'base_happiness': 50,
                'evolution_chain': {'name': None, 'url': '/evolution-chain/10'},
                'evolves_from_species': {'name': 'pichu', 'url': '/pokemon-species/172'},
                'has_gender_differences': False,
            },
            {
                'pp': 15,
                'type': {'name': 'electric', 'url': '/type/13'},
                'name': 'thunder-punch',
                'order': 9,
                'power': 75,
                'target': {'name': 'selected-pokemon', 'url': '/target/10'},
                'effect_entries': [{'flavor_text': 'Hit target', 'language': {'name': 'en', 'url': '/lang/9'}, 'short_effect': 'Hit'}],
                'damage_class': {'name': 'physical', 'url': '/damage-class/2'},
                'effect_chance': None,
                'accuracy': 100,
                'priority': 0,
            },
            {
                'id': 13,
                'moves': [],
                'names': [],
                'generation': {'name': 'generation-i', 'url': '/generation/1'},
                'game_indices': [],
                'damage_relations': {
                    'double_damage_from': [{'name': 'ground', 'url': '/type/5'}],
                    'double_damage_to': [{'name': 'water', 'url': '/type/11'}],
                    'half_damage_from': [],
                    'half_damage_to': [],
                },
                'move_damage_class': None,
            },
            {
                'id': 2,
                'name': 'medium-fast',
                'formula': 'x^3',
                'levels': [{'level': 1, 'experience': 0}],
                'descriptions': [{'description': 'Medium fast', 'language': {'name': 'en', 'url': '/lang/9'}}],
            },
            {
                'id': 10,
                'chain': {
                    'species': {'name': 'pichu', 'url': '/pokemon-species/172'},
                    'evolves_to': [
                        {
                            'species': {'name': 'pikachu', 'url': '/pokemon-species/25'},
                            'evolves_to': [],
                        }
                    ],
                },
            },
        ])

        assert (await client.get_pokemon('pikachu')).name == 'pikachu'
        assert (await client.get_pokemon_species('25')).growth_rate.name == 'medium-fast'
        assert (await client.get_move('thunder-punch')).damage_class.name == 'physical'
        assert (await client.get_type('electric')).damage_relations.double_damage_from[0].name == 'ground'
        assert (await client.get_growth_rate('medium-fast')).formula == 'x^3'
        assert (await client.get_evolution_chain('/evolution-chain/10')).chain.species.name == 'pichu'
