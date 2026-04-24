from __future__ import annotations

import logging
from datetime import datetime, timezone
from http import HTTPStatus

from fastapi import HTTPException

from app.core.cache.manager import CacheManager
from app.core.cache.service import CacheService
from app.core.exceptions import handle_service_exception
from app.core.logging import LoggingParams
from app.core.service.base import BaseService
from app.domain.pokemon.repository import PokemonRepository
from app.domain.pokemon.schema import PokemonFilterPageSchema, PokemonListSchema, PokemonSchema
from app.domain.pokemon_ability.repository import PokemonAbilityRepository
from app.domain.pokemon_growth_rate.repository import PokemonGrowthRateRepository
from app.domain.pokemon_move.repository import PokemonMoveRepository
from app.domain.pokemon_type.repository import PokemonTypeRepository
from app.infrastructure.external_api.pokeapi_client import PokeApiClient
from app.infrastructure.external_api.schemas import (
    PokemonExternalBaseAbilitySchemaResponse,
    PokemonExternalBaseMoveSchemaResponse,
    PokemonExternalBaseSpritesSchemaResponse,
    PokemonExternalBaseStatSchemaResponse,
    PokemonExternalBaseTypeSchemaResponse,
    PokemonExternalEvolutionChainLinkSchema,
)
from app.models.enums import StatusEnum
from app.models.pokemon import Pokemon
from app.models.pokemon_ability import PokemonAbility
from app.models.pokemon_growth_rate import PokemonGrowthRate
from app.models.pokemon_move import PokemonMove
from app.models.pokemon_type import PokemonType, resolve_type_colors
from app.shared.utils.image import ensure_external_image
from app.shared.utils.number import ensure_order_number

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _pick_sprite_image(sprites: PokemonExternalBaseSpritesSchemaResponse) -> str | None:
    for value in (
        sprites.front_default,
        sprites.front_shiny,
        sprites.front_female,
        sprites.back_default,
    ):
        if value:
            return value
    return None


def _extract_stat(
    stats: list[PokemonExternalBaseStatSchemaResponse], stat_name: str
) -> int | None:
    for item in stats:
        if item.stat.name == stat_name:
            return item.base_stat
    return 0


def _flatten_evolutions(
    chain: PokemonExternalEvolutionChainLinkSchema,
) -> list[str]:
    items = [chain.species.name]
    for evolution in chain.evolves_to:
        items.extend(_flatten_evolutions(evolution))
    return items


class PokemonService(BaseService[PokemonRepository, Pokemon]):
    def __init__(
        self,
        repository: PokemonRepository,
        move_repository: PokemonMoveRepository,
        ability_repository: PokemonAbilityRepository,
        type_repository: PokemonTypeRepository,
        growth_rate_repository: PokemonGrowthRateRepository,
        pokeapi_client: PokeApiClient,
    ) -> None:
        logger_params = LoggingParams(
            logger=logger,
            service='PokemonService',
            operation='pokemon',
        )
        super().__init__('pokemon', repository, logger_params, PokemonSchema)
        self.repository = repository
        self.move_repository = move_repository
        self.ability_repository = ability_repository
        self.type_repository = type_repository
        self.growth_rate_repository = growth_rate_repository
        self.pokeapi_client = pokeapi_client
        self.meta_cache = CacheManager()
        self.list_cache_service = CacheService(
            alias='pokemon',
            prefix='pokemon',
            logger_params=logger_params,
            schema_class=PokemonListSchema,
        )

    async def total(self) -> int:
        return await self.repository.total()

    async def initialize_list(self, total: int = 0, external_total: int = 1350):
        external_pokemons = await self.pokeapi_client.list_pokemon(offset=0, limit=external_total)

        if total == 0:
            for result in external_pokemons:
                await self.repository.create(
                    {
                        'name': result.name,
                        'order': ensure_order_number(result.url),
                        'status': StatusEnum.INCOMPLETE,
                        'external_image': ensure_external_image(
                            ensure_order_number(result.url)
                        ),
                    }
                )
            return await self.repository.list_all()

        if total < external_total:
            for result in external_pokemons:
                order = ensure_order_number(result.url)
                existing = await self.repository.find_by(order=order)
                if existing is not None:
                    continue
                await self.repository.create(
                    {
                        'name': result.name,
                        'order': order,
                        'status': StatusEnum.INCOMPLETE,
                        'external_image': ensure_external_image(order),
                    }
                )

        return await self.repository.list_all()

    async def list_sync(self) -> bool:
        cache_key = 'pokemon:meta'
        cached = await self.meta_cache.get_cache(cache_key)
        if cached:
            return False

        total = await self.total()
        external_total = await self.pokeapi_client.total()
        await self.meta_cache.set_cache(
            cache_key,
            {'total': total, 'external_total': external_total},
            ttl=3600,
        )

        if total == 0:
            await self.initialize_list(total=0, external_total=external_total)
            return True

        if total < external_total:
            await self.initialize_list(total=total, external_total=external_total)
            await self.meta_cache.set_cache(
                cache_key,
                {'total': await self.total(), 'external_total': external_total},
                ttl=3600,
            )
            return True

        return False

    async def list(
        self,
        page_filter: PokemonFilterPageSchema | None = None,
        user_request: str | None = None,
    ):
        try:
            await self.list_sync()
            filter_page = PokemonFilterPageSchema.build(page_filter)
            return await self.repository.list_all(page_filter=filter_page)
        except Exception as exception:
            handle_service_exception(
                exception,
                logger=logger,
                service='PokemonService',
                operation='list',
                user_request=user_request,
                raise_exception=True,
            )

    async def list_cached(
        self,
        page_filter: PokemonFilterPageSchema | None = None,
        user_request: str | None = None,
    ):
        filter_page = PokemonFilterPageSchema.build(page_filter)
        key = self.list_cache_service.build_key_list(page_filter=filter_page)
        cached = await self.list_cache_service.get_list(key)
        if cached:
            return cached
        result = await self.list(page_filter=filter_page, user_request=user_request)
        await self.list_cache_service.set_list(key, result)
        return result

    async def get(self, name_or_id: str) -> Pokemon:
        pokemon = await self.find_one(name_or_id)
        if pokemon.status == StatusEnum.INCOMPLETE:
            return await self.complete_pokemon(pokemon.name)
        return pokemon

    async def complete_pokemon(self, name: str, with_evolutions: bool = True) -> Pokemon:
        pokemon = await self.repository.find_by(name=name)
        if pokemon is None:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='pokemon not found',
            )

        try:
            external_pokemon = await self.pokeapi_client.get_pokemon(name)
            species = await self.pokeapi_client.get_pokemon_species(name)

            moves = await self.add_moves(external_pokemon.moves)
            abilities = await self.add_abilities(external_pokemon.abilities)
            types = await self.add_types(external_pokemon.types)
            growth_rate = await self.add_growth_rate(species.growth_rate)

            pokemon.hp = _extract_stat(external_pokemon.stats, 'hp')
            pokemon.image = _pick_sprite_image(external_pokemon.sprites)
            pokemon.speed = _extract_stat(external_pokemon.stats, 'speed')
            pokemon.height = external_pokemon.height
            pokemon.weight = external_pokemon.weight
            pokemon.attack = _extract_stat(external_pokemon.stats, 'attack')
            pokemon.defense = _extract_stat(external_pokemon.stats, 'defense')
            pokemon.habitat = species.habitat.name if species.habitat else None
            pokemon.is_baby = species.is_baby
            pokemon.shape_url = species.shape.url if species.shape else None
            pokemon.shape_name = species.shape.name if species.shape else None
            pokemon.is_mythical = species.is_mythical
            pokemon.gender_rate = species.gender_rate
            pokemon.is_legendary = species.is_legendary
            pokemon.capture_rate = species.capture_rate
            pokemon.hatch_counter = species.hatch_counter
            pokemon.base_happiness = species.base_happiness
            pokemon.special_attack = _extract_stat(external_pokemon.stats, 'special-attack')
            pokemon.base_experience = external_pokemon.base_experience
            pokemon.special_defense = _extract_stat(
                external_pokemon.stats, 'special-defense'
            )
            pokemon.evolution_chain = (
                species.evolution_chain.url if species.evolution_chain else None
            )
            pokemon.evolves_from_species = (
                species.evolves_from_species.name if species.evolves_from_species else None
            )
            pokemon.has_gender_differences = species.has_gender_differences
            pokemon.growth_rate = growth_rate
            pokemon.moves = moves
            pokemon.abilities = abilities
            pokemon.types = types
            pokemon.status = StatusEnum.COMPLETE
            pokemon.updated_at = _utcnow()

            if with_evolutions and pokemon.evolution_chain:
                pokemon.evolutions = await self.add_evolutions(pokemon.evolution_chain, pokemon.name)

            return await self.repository.update(pokemon)
        except HTTPException:
            raise
        except Exception as exception:
            raise HTTPException(
                status_code=HTTPStatus.BAD_GATEWAY,
                detail=f'Failed to complete pokemon {name}: {exception}',
            ) from exception

    async def add_moves(
        self, move_refs: list[PokemonExternalBaseMoveSchemaResponse]
    ) -> list[PokemonMove]:
        moves: list[PokemonMove] = []
        for move_ref in move_refs[:20]:
            move_name = move_ref.move.name
            existing = await self.move_repository.find_by(name=move_name)
            if existing is not None:
                moves.append(existing)
                continue

            external_move = await self.pokeapi_client.get_move(move_name)
            effect_entry = next(
                (
                    item
                    for item in external_move.effect_entries
                    if item.language.name == 'en'
                ),
                None,
            )
            move_order = external_move.order
            if move_order is None:
                move_order = ensure_order_number(f'{move_ref.move.url.rstrip("/")}/')

            created = await self.move_repository.create(
                {
                    'pp': external_move.pp or 0,
                    'url': move_ref.move.url,
                    'type': external_move.type.name,
                    'name': external_move.name,
                    'order': move_order,
                    'power': external_move.power or 0,
                    'target': external_move.target.name,
                    'effect': effect_entry.effect if effect_entry else '',
                    'priority': external_move.priority,
                    'accuracy': external_move.accuracy or 0,
                    'short_effect': effect_entry.short_effect if effect_entry else '',
                    'damage_class': external_move.damage_class.name,
                    'effect_chance': external_move.effect_chance,
                }
            )
            moves.append(created)
        return moves

    async def add_abilities(
        self, ability_refs: list[PokemonExternalBaseAbilitySchemaResponse]
    ) -> list[PokemonAbility]:
        abilities: list[PokemonAbility] = []
        for index, ability_ref in enumerate(ability_refs, start=1):
            existing = await self.ability_repository.find_by(name=ability_ref.ability.name)
            if existing is not None:
                abilities.append(existing)
                continue
            created = await self.ability_repository.create(
                {
                    'url': ability_ref.ability.url,
                    'order': index,
                    'name': ability_ref.ability.name,
                    'slot': ability_ref.slot,
                    'is_hidden': ability_ref.is_hidden,
                }
            )
            abilities.append(created)
        return abilities

    async def add_types(
        self, type_refs: list[PokemonExternalBaseTypeSchemaResponse]
    ) -> list[PokemonType]:
        types: list[PokemonType] = []
        for type_ref in type_refs:
            existing = await self.type_repository.find_by(name=type_ref.type.name)
            if existing is not None:
                types.append(existing)
                continue

            external_type = await self.pokeapi_client.get_type(type_ref.type.name)
            background_color, text_color = resolve_type_colors(type_ref.type.name)
            created = await self.type_repository.create(
                {
                    'url': type_ref.type.url,
                    'order': external_type.id,
                    'name': type_ref.type.name,
                    'text_color': text_color,
                    'background_color': background_color,
                }
            )
            created.weaknesses = await self._resolve_type_relations(
                external_type.damage_relations.double_damage_from
                + external_type.damage_relations.half_damage_from
            )
            created.strengths = await self._resolve_type_relations(
                external_type.damage_relations.double_damage_to
                + external_type.damage_relations.half_damage_to
            )
            created = await self.type_repository.update(created)
            types.append(created)
        return types

    async def _resolve_type_relations(
        self, resources: list
    ) -> list[PokemonType]:
        related_types: list[PokemonType] = []
        for resource in resources:
            existing = await self.type_repository.find_by(name=resource.name)
            if existing is not None:
                related_types.append(existing)
                continue
            background_color, text_color = resolve_type_colors(resource.name)
            created = await self.type_repository.create(
                {
                    'url': resource.url,
                    'order': ensure_order_number(resource.url),
                    'name': resource.name,
                    'text_color': text_color,
                    'background_color': background_color,
                }
            )
            related_types.append(created)
        return related_types

    async def add_growth_rate(
        self, growth_rate_ref
    ) -> PokemonGrowthRate | None:
        if growth_rate_ref is None:
            return None
        existing = await self.growth_rate_repository.find_by(name=growth_rate_ref.name)
        if existing is not None:
            return existing
        external_growth_rate = await self.pokeapi_client.get_growth_rate(growth_rate_ref.name)
        description = next(
            (
                item.description
                for item in external_growth_rate.descriptions
                if item.language.name == 'en'
            ),
            external_growth_rate.name,
        )
        return await self.growth_rate_repository.create(
            {
                'url': growth_rate_ref.url,
                'name': external_growth_rate.name,
                'formula': external_growth_rate.formula,
                'description': description,
            }
        )

    async def add_evolutions(
        self, evolution_chain_url: str, current_name: str
    ) -> list[Pokemon]:
        external_chain = await self.pokeapi_client.get_evolution_chain(evolution_chain_url)
        names = [name for name in _flatten_evolutions(external_chain.chain) if name != current_name]
        evolutions: list[Pokemon] = []
        for name in names:
            pokemon = await self.repository.find_by(name=name)
            if pokemon is not None:
                evolutions.append(pokemon)
                continue
            external_detail = await self.pokeapi_client.get_pokemon(name)
            pokemon = await self.repository.create(
                {
                    'name': external_detail.name,
                    'order': external_detail.order,
                    'status': StatusEnum.INCOMPLETE,
                    'external_image': ensure_external_image(external_detail.order),
                }
            )
            evolutions.append(pokemon)
        return evolutions
