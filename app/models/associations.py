from sqlalchemy import Column, ForeignKey, Table, Uuid

from app.core.database.base import table_registry

metadata = table_registry.metadata

pokemon_pokemon_moves = Table(
    'pokemon_pokemon_moves',
    metadata,
    Column('pokemon_id', Uuid, ForeignKey('pokemons.id'), primary_key=True),
    Column('pokemon_move_id', Uuid, ForeignKey('pokemon_moves.id'), primary_key=True),
)

pokemon_pokemon_abilities = Table(
    'pokemon_pokemon_abilities',
    metadata,
    Column('pokemon_id', Uuid, ForeignKey('pokemons.id'), primary_key=True),
    Column('pokemon_ability_id', Uuid, ForeignKey('pokemon_abilities.id'), primary_key=True),
)

pokemon_pokemon_types = Table(
    'pokemon_pokemon_types',
    metadata,
    Column('pokemon_id', Uuid, ForeignKey('pokemons.id'), primary_key=True),
    Column('pokemon_type_id', Uuid, ForeignKey('pokemon_types.id'), primary_key=True),
)

pokemon_type_weaknesses = Table(
    'pokemon_type_weaknesses',
    metadata,
    Column('type_id', Uuid, ForeignKey('pokemon_types.id'), primary_key=True),
    Column('weak_against_id', Uuid, ForeignKey('pokemon_types.id'), primary_key=True),
)

pokemon_type_strengths = Table(
    'pokemon_type_strengths',
    metadata,
    Column('type_id', Uuid, ForeignKey('pokemon_types.id'), primary_key=True),
    Column('strong_against_id', Uuid, ForeignKey('pokemon_types.id'), primary_key=True),
)

pokemon_evolutions = Table(
    'pokemon_evolutions',
    metadata,
    Column('pokemon_id', Uuid, ForeignKey('pokemons.id'), primary_key=True),
    Column('evolution_id', Uuid, ForeignKey('pokemons.id'), primary_key=True),
)

my_pokemon_pokemon_moves = Table(
    'my_pokemon_pokemon_moves',
    metadata,
    Column('my_pokemon_id', Uuid, ForeignKey('my_pokemons.id'), primary_key=True),
    Column('pokemon_move_id', Uuid, ForeignKey('pokemon_moves.id'), primary_key=True),
)
