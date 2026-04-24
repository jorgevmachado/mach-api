from __future__ import annotations

from http import HTTPStatus
from typing import Any

import httpx
from fastapi import HTTPException

from app.core.settings import Settings
from app.infrastructure.external_api.schemas import (
    PokemonExternalBaseSchema,
    PokemonExternalEvolutionSchema,
    PokemonExternalGrowthRateSchemaResponse,
    PokemonExternalListSchema,
    PokemonExternalMoveSchemaResponse,
    PokemonExternalSchema,
    PokemonExternalSpecieSchema,
    PokemonExternalTypeSchemaResponse,
)
from app.shared.utils.image import ensure_external_image
from app.shared.utils.number import ensure_order_number


class PokeApiClient:
    def __init__(
        self,
        base_url: str | None = None,
        *,
        verify_ssl: bool | str | None = None,
    ) -> None:
        settings = Settings()
        self.base_url = (base_url or settings.POKEAPI_BASE_URL).rstrip('/')
        self.verify_ssl = (
            verify_ssl
            if verify_ssl is not None
            else (
                settings.POKEAPI_CA_BUNDLE
                if settings.POKEAPI_CA_BUNDLE
                else settings.POKEAPI_VERIFY_SSL
            )
        )

    async def _request(self, path: str) -> dict[str, Any]:
        url = path if path.startswith('http') else f'{self.base_url}/{path.lstrip("/")}'
        try:
            async with httpx.AsyncClient(
                timeout=20.0,
                verify=self.verify_ssl,
                trust_env=True,
            ) as client:
                response = await client.get(url)
        except httpx.HTTPError as exception:
            ssl_hint = ''
            if 'CERTIFICATE_VERIFY_FAILED' in str(exception):
                ssl_hint = (
                    ' Configure POKEAPI_CA_BUNDLE with your CA bundle path or set '
                    'POKEAPI_VERIFY_SSL=false only in environments that require it.'
                )
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail=f'PokeAPI request failed for {url}: {exception}.{ssl_hint}',
            ) from exception

        if response.status_code == HTTPStatus.NOT_FOUND:
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail=f'PokeAPI resource not found for {url}',
            )

        if not response.is_success:
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail=f'PokeAPI returned status {response.status_code} for {url}',
            )

        return response.json()

    async def list_pokemon(self, offset: int = 0, limit: int = 1350) -> list[PokemonExternalBaseSchema]:
        payload = await self._request(f'pokemon?offset={offset}&limit={limit}')
        parsed = PokemonExternalListSchema.model_validate(payload)
        return [
            PokemonExternalBaseSchema(
                url=item.url,
                order=ensure_order_number(item.url),
                name=item.name,
                external_image=ensure_external_image(ensure_order_number(item.url)),
            )
            for item in parsed.results
        ]

    async def total(self) -> int:
        payload = await self._request('pokemon?offset=0&limit=1')
        parsed = PokemonExternalListSchema.model_validate(payload)
        return parsed.count

    async def get_pokemon(self, name: str) -> PokemonExternalSchema:
        payload = await self._request(f'pokemon/{name}')
        return PokemonExternalSchema.model_validate(payload)

    async def get_pokemon_species(self, name_or_id: str) -> PokemonExternalSpecieSchema:
        payload = await self._request(f'pokemon-species/{name_or_id}')
        return PokemonExternalSpecieSchema.model_validate(payload)

    async def get_move(self, order_or_name: int | str) -> PokemonExternalMoveSchemaResponse:
        payload = await self._request(f'move/{order_or_name}')
        return PokemonExternalMoveSchemaResponse.model_validate(payload)

    async def get_type(self, order_or_name: int | str) -> PokemonExternalTypeSchemaResponse:
        payload = await self._request(f'type/{order_or_name}')
        return PokemonExternalTypeSchemaResponse.model_validate(payload)

    async def get_growth_rate(
        self, order_or_name: int | str
    ) -> PokemonExternalGrowthRateSchemaResponse:
        payload = await self._request(f'growth-rate/{order_or_name}')
        return PokemonExternalGrowthRateSchemaResponse.model_validate(payload)

    async def get_evolution_chain(self, url: str) -> PokemonExternalEvolutionSchema:
        payload = await self._request(url)
        return PokemonExternalEvolutionSchema.model_validate(payload)
