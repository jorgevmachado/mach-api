from __future__ import annotations

import logging

from app.core.logging import LoggingParams
from app.core.service.base import BaseService
from app.domain.pokemon_growth_rate.repository import PokemonGrowthRateRepository
from app.domain.pokemon_growth_rate.schema import PokemonGrowthRateSchema
from app.models.pokemon_growth_rate import PokemonGrowthRate

logger = logging.getLogger(__name__)


class PokemonGrowthRateService(
    BaseService[PokemonGrowthRateRepository, PokemonGrowthRate]
):
    def __init__(self, repository: PokemonGrowthRateRepository) -> None:
        super().__init__(
            'pokemon_growth_rate',
            repository,
            LoggingParams(
                logger=logger,
                service='PokemonGrowthRateService',
                operation='growth_rate',
            ),
            PokemonGrowthRateSchema,
        )
