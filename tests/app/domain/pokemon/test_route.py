from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.routing import APIRoute
from fastapi_pagination import LimitOffsetParams

from app.core.pagination.schemas import CustomLimitOffsetPage
from app.core.security import get_current_user
from app.domain.pokemon.route import (
    get_pokemon,
    list_moves,
    list_pokemon,
    router,
)
from app.domain.pokemon.schema import PokemonFilterPageSchema
from app.models.enums import StatusEnum


@pytest.fixture
def authenticated_user():
    return {
        'id': str(uuid4()),
        'name': 'Ash Ketchum',
        'email': 'ash@example.com',
        'username': 'ash',
        'status': StatusEnum.COMPLETE,
    }


class TestPokemonRoutes:
    @staticmethod
    def test_list_pokemon_route_requires_authentication_dependency():
        list_route = next(
            route for route in router.routes
            if isinstance(route, APIRoute) and route.path == '' and 'GET' in route.methods
        )

        dependency_calls = [dependency.call for dependency in list_route.dependant.dependencies]

        assert get_current_user in dependency_calls

    @staticmethod
    @pytest.mark.asyncio
    async def test_list_pokemon_returns_paginated_payload(authenticated_user):
        service = AsyncMock()
        service.list_cached = AsyncMock(
            return_value=CustomLimitOffsetPage.create(
                items=[
                    {
                        'id': str(uuid4()),
                        'name': 'pikachu',
                        'order': 25,
                        'status': 'INCOMPLETE',
                        'external_image': 'https://image/pikachu.png',
                        'moves': [],
                        'abilities': [],
                        'types': [],
                        'evolutions': [],
                        'created_at': '2026-04-23T00:00:00Z',
                    }
                ],
                total=1,
                params=LimitOffsetParams(limit=12, offset=0),
            )
        )

        response = await list_pokemon(
            _=authenticated_user,
            service=service,
            page_filter=PokemonFilterPageSchema(page=1, limit=12),
        )

        assert response.items[0]['name'] == 'pikachu'
        assert response.meta.current_page == 1

    @staticmethod
    @pytest.mark.asyncio
    async def test_get_pokemon_returns_detail(authenticated_user):
        service = AsyncMock()
        service.get = AsyncMock(
            return_value={
                'id': str(uuid4()),
                'name': 'pikachu',
                'order': 25,
                'status': 'COMPLETE',
                'external_image': 'https://image/pikachu.png',
                'moves': [
                    {
                        'id': str(uuid4()),
                        'name': 'quick-attack',
                        'pp': 30,
                        'url': '/move/98',
                        'type': 'normal',
                        'order': 98,
                        'power': 40,
                        'target': 'selected-pokemon',
                        'effect': 'Inflicts regular damage.',
                        'priority': 1,
                        'accuracy': 100,
                        'short_effect': 'Usually goes first.',
                        'damage_class': 'physical',
                        'effect_chance': None,
                        'created_at': '2026-04-23T00:00:00Z',
                    }
                ],
                'abilities': [
                    {
                        'id': str(uuid4()),
                        'url': '/ability/9',
                        'order': 1,
                        'name': 'static',
                        'slot': 1,
                        'is_hidden': False,
                        'created_at': '2026-04-23T00:00:00Z',
                    }
                ],
                'types': [
                    {
                        'id': str(uuid4()),
                        'url': '/type/13',
                        'order': 13,
                        'name': 'electric',
                        'text_color': '#212121',
                        'background_color': '#F8D030',
                        'weaknesses': [
                            {
                                'id': str(uuid4()),
                                'name': 'ground',
                                'text_color': '#f5f5f5',
                                'background_color': '#bc5e00',
                            }
                        ],
                        'strengths': [],
                        'created_at': '2026-04-23T00:00:00Z',
                    }
                ],
                'evolutions': [
                    {
                        'id': str(uuid4()),
                        'name': 'raichu',
                        'order': 26,
                        'status': 'COMPLETE',
                        'external_image': 'https://image/raichu.png',
                        'image': 'https://image/raichu-sprite.png',
                    }
                ],
                'created_at': '2026-04-23T00:00:00Z',
            }
        )

        response = await get_pokemon(
            name_or_id='pikachu',
            _=authenticated_user,
            service=service,
        )

        assert response['name'] == 'pikachu'
        assert response['moves'][0]['damage_class'] == 'physical'
        assert response['types'][0]['weaknesses'][0]['background_color'] == '#bc5e00'
        assert response['evolutions'][0]['external_image'] == 'https://image/raichu.png'


class TestPokemonRelatedResourceRoutes:
    @staticmethod
    @pytest.mark.asyncio
    async def test_list_moves_returns_protected_collection(authenticated_user):
        service = AsyncMock()
        service.list_all = AsyncMock(
            return_value=[
                {
                    'id': str(uuid4()),
                    'name': 'thunder-punch',
                    'pp': 15,
                    'url': 'https://pokeapi.co/api/v2/move/9/',
                    'type': 'electric',
                    'order': 9,
                    'power': 75,
                    'target': 'selected-pokemon',
                    'effect': 'Hit target',
                    'priority': 0,
                    'accuracy': 100,
                    'short_effect': 'Hit target',
                    'damage_class': 'physical',
                    'created_at': '2026-04-23T00:00:00Z',
                }
            ]
        )

        response = await list_moves(
            _=authenticated_user,
            service=service,
        )

        assert response[0]['name'] == 'thunder-punch'
