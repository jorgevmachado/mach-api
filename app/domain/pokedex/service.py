from __future__ import annotations

import logging
from datetime import datetime, timezone
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException

from app.core.logging import LoggingParams
from app.core.service.base import BaseService
from app.domain.pokedex.business import initialize_species_progression
from app.domain.pokedex.repository import PokedexRepository
from app.domain.pokedex.schema import (
    PokedexDetailSchema,
    PokedexFilterPageSchema,
    PokedexSchema,
    PokedexUpdateSchema,
)
from app.domain.pokemon.repository import PokemonRepository
from app.domain.trainer.repository import TrainerRepository
from app.models.pokedex import Pokedex

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PokedexService(BaseService[PokedexRepository, Pokedex]):
    def __init__(
        self,
        repository: PokedexRepository,
        pokemon_repository: PokemonRepository,
        trainer_repository: TrainerRepository,
    ) -> None:
        logger_params = LoggingParams(
            logger=logger,
            service='PokedexService',
            operation='pokedex',
        )
        super().__init__('pokedex', repository, logger_params, PokedexSchema)
        self.repository = repository
        self.pokemon_repository = pokemon_repository
        self.trainer_repository = trainer_repository

    async def initialize_for_trainer(self, trainer_id: UUID, starter_name: str) -> None:
        try:
            pokemons = await self.pokemon_repository.list_all()
            existing_entries = await self.repository.list_all(
                page_filter=PokedexFilterPageSchema.build(None, trainer_id=str(trainer_id))
            )
            entries_by_pokemon_id = {
                entry.pokemon_id: entry for entry in existing_entries if entry.deleted_at is None
            }

            for pokemon in pokemons:
                discovered = pokemon.name == starter_name
                existing = entries_by_pokemon_id.get(pokemon.id)

                if existing is not None:
                    if discovered and not existing.discovered:
                        existing.discovered = True
                        existing.discovered_at = _utcnow()
                        existing.updated_at = _utcnow()
                    continue

                payload = initialize_species_progression(pokemon, discovered=discovered)
                self.repository.session.add(
                    Pokedex(
                        **payload,
                        trainer_id=trainer_id,
                        pokemon_id=pokemon.id,
                    )
                )

            await self.repository.session.commit()
        except Exception:
            await self.repository.session.rollback()
            raise

    async def list_trainer(
        self,
        trainer_id: UUID,
        page_filter: PokedexFilterPageSchema | None = None,
    ):
        filter_page = PokedexFilterPageSchema.build(page_filter, trainer_id=str(trainer_id))
        return await self.repository.list_all(page_filter=filter_page)

    async def get_trainer(self, entry_id: str, trainer_id: UUID) -> PokedexDetailSchema:
        entry = await self.repository.find_by(id=entry_id, trainer_id=trainer_id)
        if entry is None or entry.deleted_at is not None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Pokedex not found')
        if not entry.discovered:
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail='Pokedex entry not discovered')
        return PokedexDetailSchema.model_validate(entry)

    async def discover(self, trainer_id: UUID, pokemon_id: UUID) -> None:
        entry = await self.repository.find_by(trainer_id=trainer_id, pokemon_id=pokemon_id)
        if entry is None or entry.discovered:
            return

        entry.discovered = True
        entry.discovered_at = _utcnow()
        entry.updated_at = _utcnow()
        await self.repository.update(entry)

    async def update_trainer(
        self,
        entry_id: str,
        trainer_id: UUID,
        data: PokedexUpdateSchema,
    ) -> PokedexSchema:
        entry = await self.repository.find_by(id=entry_id, trainer_id=trainer_id)
        if entry is None or entry.deleted_at is not None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Pokedex not found')

        update_data = data.model_dump(exclude_none=True)
        discovered_before = entry.discovered
        for key, value in update_data.items():
            setattr(entry, key, value)

        if not discovered_before and entry.discovered:
            entry.discovered_at = _utcnow()

        entry.updated_at = _utcnow()
        return PokedexSchema.model_validate(await self.repository.update(entry))

    async def soft_delete_trainer(self, entry_id: str, trainer_id: UUID) -> dict[str, str]:
        entry = await self.repository.find_by(id=entry_id, trainer_id=trainer_id)
        if entry is None or entry.deleted_at is not None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='Pokedex not found')

        entry.deleted_at = _utcnow()
        entry.updated_at = _utcnow()
        await self.repository.update(entry)
        return {'message': 'Pokedex deleted successfully'}
