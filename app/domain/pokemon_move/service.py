from __future__ import annotations

import logging

from app.core.logging import LoggingParams
from app.core.service.base import BaseService
from app.domain.pokemon_move.repository import PokemonMoveRepository
from app.domain.pokemon_move.schema import PokemonMoveSchema
from app.models.pokemon_move import PokemonMove

logger = logging.getLogger(__name__)


class PokemonMoveService(BaseService[PokemonMoveRepository, PokemonMove]):
    def __init__(self, repository: PokemonMoveRepository) -> None:
        super().__init__(
            'pokemon_move',
            repository,
            LoggingParams(logger=logger, service='PokemonMoveService', operation='move'),
            PokemonMoveSchema,
        )
