from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class NamedApiResourceSchema(BaseModel):
    name: str | None = None
    url: str


class PokemonExternalBaseSchema(BaseModel):
    url: str
    order: int
    name: str
    external_image: str


class PokemonExternalBaseTypeSchemaResponse(BaseModel):
    type: NamedApiResourceSchema
    slot: int


class PokemonExternalBaseMoveSchemaResponse(BaseModel):
    move: NamedApiResourceSchema


class PokemonExternalBaseAbilitySchemaResponse(BaseModel):
    slot: int
    ability: NamedApiResourceSchema
    is_hidden: bool


class PokemonExternalBaseStatSchemaResponse(BaseModel):
    stat: NamedApiResourceSchema
    base_stat: int


class PokemonExternalBaseSpritesSchemaResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    back_gray: str | None = Field(default=None, alias='back_gray')
    front_gray: str | None = Field(default=None, alias='front_gray')
    back_shiny: str | None = None
    front_shiny: str | None = None
    back_female: str | None = None
    front_female: str | None = None
    back_default: str | None = None
    front_default: str | None = None
    back_transparent: str | None = None
    front_transparent: str | None = None
    back_shiny_female: str | None = None
    front_shiny_female: str | None = None
    back_shiny_transparent: str | None = None
    front_shiny_transparent: str | None = None


class PokemonExternalSchema(BaseModel):
    name: str
    order: int
    types: list[PokemonExternalBaseTypeSchemaResponse]
    moves: list[PokemonExternalBaseMoveSchemaResponse]
    stats: list[PokemonExternalBaseStatSchemaResponse]
    height: int
    weight: int
    sprites: PokemonExternalBaseSpritesSchemaResponse
    abilities: list[PokemonExternalBaseAbilitySchemaResponse]
    base_experience: int


class PokemonExternalSpecieSchema(BaseModel):
    name: str
    shape: NamedApiResourceSchema | None = None
    habitat: NamedApiResourceSchema | None = None
    is_baby: bool
    growth_rate: NamedApiResourceSchema | None = None
    gender_rate: int
    is_mythical: bool
    capture_rate: int
    is_legendary: bool
    hatch_counter: int
    base_happiness: int
    evolution_chain: NamedApiResourceSchema | None = None
    evolves_from_species: NamedApiResourceSchema | None = None
    has_gender_differences: bool


class PokemonExternalEffectEntrySchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    effect: str = Field(validation_alias=AliasChoices('effect', 'flavor_text'))
    language: NamedApiResourceSchema
    short_effect: str | None = None


class PokemonExternalMoveSchemaResponse(BaseModel):
    pp: int | None = 0
    type: NamedApiResourceSchema
    name: str
    order: int | None = None
    power: int | None = 0
    target: NamedApiResourceSchema
    effect_entries: list[PokemonExternalEffectEntrySchema]
    damage_class: NamedApiResourceSchema
    effect_chance: int | None = None
    accuracy: int | None = 0
    priority: int = 0


class PokemonExternalGrowthRateLevelSchema(BaseModel):
    level: int
    experience: int


class PokemonExternalDescriptionSchema(BaseModel):
    description: str
    language: NamedApiResourceSchema


class PokemonExternalGrowthRateSchemaResponse(BaseModel):
    id: int
    name: str
    formula: str
    levels: list[PokemonExternalGrowthRateLevelSchema]
    descriptions: list[PokemonExternalDescriptionSchema]


class PokemonExternalGameIndexSchema(BaseModel):
    game_index: int
    generation: NamedApiResourceSchema


class PokemonExternalDamageRelationsSchema(BaseModel):
    double_damage_from: list[NamedApiResourceSchema] = []
    double_damage_to: list[NamedApiResourceSchema] = []
    half_damage_from: list[NamedApiResourceSchema] = []
    half_damage_to: list[NamedApiResourceSchema] = []


class PokemonExternalTypeSchemaResponse(BaseModel):
    id: int
    moves: list[NamedApiResourceSchema]
    names: list[dict[str, Any]]
    generation: NamedApiResourceSchema
    game_indices: list[PokemonExternalGameIndexSchema]
    damage_relations: PokemonExternalDamageRelationsSchema
    move_damage_class: NamedApiResourceSchema | None = None


class PokemonExternalEvolutionChainLinkSchema(BaseModel):
    species: NamedApiResourceSchema
    evolves_to: list['PokemonExternalEvolutionChainLinkSchema'] = []


class PokemonExternalEvolutionSchema(BaseModel):
    id: int
    chain: PokemonExternalEvolutionChainLinkSchema


class PokemonExternalListSchema(BaseModel):
    count: int
    results: list[NamedApiResourceSchema]


PokemonExternalEvolutionChainLinkSchema.model_rebuild()
