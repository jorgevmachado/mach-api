from __future__ import annotations

import logging

from app.core.logging import LoggingParams
from app.core.service.base import BaseService
from app.domain.pokemon_type.repository import PokemonTypeRepository
from app.domain.pokemon_type.schema import PokemonTypeSchema
from app.models.pokemon_type import PokemonType

logger = logging.getLogger(__name__)


class PokemonTypeService(BaseService[PokemonTypeRepository, PokemonType]):
    def __init__(self, repository: PokemonTypeRepository) -> None:
        super().__init__(
            'pokemon_type',
            repository,
            LoggingParams(logger=logger, service='PokemonTypeService', operation='type'),
            PokemonTypeSchema,
        )
