from __future__ import annotations

import logging
from datetime import datetime, timezone
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException

from app.core.logging import LoggingParams
from app.core.service.base import BaseService
from app.domain.my_pokemon.business import (
    build_default_nickname,
    initialize_instance_progression,
    pick_equipped_moves,
)
from app.domain.my_pokemon.repository import MyPokemonRepository
from app.domain.my_pokemon.schema import (
    MyPokemonDetailSchema,
    MyPokemonFilterPageSchema,
    MyPokemonSchema,
    MyPokemonUpdateSchema,
)
from app.domain.pokedex.service import PokedexService
from app.models.my_pokemon import MyPokemon
from app.models.pokemon import Pokemon

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MyPokemonService(BaseService[MyPokemonRepository, MyPokemon]):
    def __init__(
        self,
        repository: MyPokemonRepository,
        pokedex_service: PokedexService,
    ) -> None:
        logger_params = LoggingParams(
            logger=logger,
            service='MyPokemonService',
            operation='my_pokemon',
        )
        super().__init__('my_pokemon', repository, logger_params, MyPokemonSchema)
        self.repository = repository
        self.pokedex_service = pokedex_service

    async def capture(
        self,
        trainer_id: UUID,
        pokemon: Pokemon,
        *,
        nickname: str | None = None,
    ) -> MyPokemon:
        resolved_nickname = nickname.strip() if nickname else build_default_nickname(pokemon.name)
        payload = initialize_instance_progression(pokemon, nickname=resolved_nickname)
        captured = await self.repository.create(
            {
                **payload,
                'trainer_id': trainer_id,
                'pokemon_id': pokemon.id,
            }
        )
        captured.moves = pick_equipped_moves(pokemon.moves)
        captured.updated_at = _utcnow()
        captured = await self.repository.update(captured)

        await self.pokedex_service.discover(trainer_id, pokemon.id)

        return captured

    async def list_trainer(
        self,
        trainer_id: UUID,
        page_filter: MyPokemonFilterPageSchema | None = None,
    ):
        filter_page = MyPokemonFilterPageSchema.build(page_filter, trainer_id=str(trainer_id))
        return await self.repository.list_all(page_filter=filter_page)

    async def get_trainer(self, entry_id: str, trainer_id: UUID) -> MyPokemonDetailSchema:
        entry = await self.repository.find_by(id=entry_id, trainer_id=trainer_id)
        if entry is None or entry.deleted_at is not None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='MyPokemon not found')
        return MyPokemonDetailSchema.model_validate(entry)

    async def update_trainer(
        self,
        entry_id: str,
        trainer_id: UUID,
        data: MyPokemonUpdateSchema,
    ) -> MyPokemonSchema:
        entry = await self.repository.find_by(id=entry_id, trainer_id=trainer_id)
        if entry is None or entry.deleted_at is not None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='MyPokemon not found')

        entry.nickname = data.nickname
        entry.updated_at = _utcnow()
        return MyPokemonSchema.model_validate(await self.repository.update(entry))

    async def soft_delete_trainer(self, entry_id: str, trainer_id: UUID) -> dict[str, str]:
        entry = await self.repository.find_by(id=entry_id, trainer_id=trainer_id)
        if entry is None or entry.deleted_at is not None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='MyPokemon not found')

        entry.deleted_at = _utcnow()
        entry.updated_at = _utcnow()
        await self.repository.update(entry)
        return {'message': 'MyPokemon deleted successfully'}
