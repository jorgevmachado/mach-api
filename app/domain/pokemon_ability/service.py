from __future__ import annotations

import logging

from app.core.logging import LoggingParams
from app.core.service.base import BaseService
from app.domain.pokemon_ability.repository import PokemonAbilityRepository
from app.domain.pokemon_ability.schema import PokemonAbilitySchema
from app.models.pokemon_ability import PokemonAbility

logger = logging.getLogger(__name__)


class PokemonAbilityService(BaseService[PokemonAbilityRepository, PokemonAbility]):
    def __init__(self, repository: PokemonAbilityRepository) -> None:
        super().__init__(
            'pokemon_ability',
            repository,
            LoggingParams(
                logger=logger,
                service='PokemonAbilityService',
                operation='ability',
            ),
            PokemonAbilitySchema,
        )
