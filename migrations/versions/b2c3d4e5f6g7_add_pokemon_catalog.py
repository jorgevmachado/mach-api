"""add pokemon catalog

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-23 19:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pokemon_growth_rates (
            id uuid PRIMARY KEY,
            url TEXT NOT NULL,
            name TEXT NOT NULL UNIQUE,
            formula TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz,
            deleted_at timestamptz
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pokemon_moves (
            id uuid PRIMARY KEY,
            pp integer NOT NULL,
            url TEXT NOT NULL,
            type TEXT NOT NULL,
            name TEXT NOT NULL UNIQUE,
            "order" integer NOT NULL,
            power integer NOT NULL,
            target TEXT NOT NULL,
            effect TEXT NOT NULL,
            priority integer NOT NULL,
            accuracy integer NOT NULL,
            short_effect TEXT NOT NULL,
            damage_class TEXT NOT NULL,
            effect_chance integer,
            created_at timestamptz NOT NULL,
            updated_at timestamptz,
            deleted_at timestamptz
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pokemon_abilities (
            id uuid PRIMARY KEY,
            url TEXT NOT NULL,
            "order" integer NOT NULL,
            name TEXT NOT NULL UNIQUE,
            slot integer NOT NULL,
            is_hidden boolean NOT NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz,
            deleted_at timestamptz
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pokemon_types (
            id uuid PRIMARY KEY,
            url TEXT NOT NULL,
            "order" integer NOT NULL,
            name TEXT NOT NULL UNIQUE,
            text_color TEXT NOT NULL,
            background_color TEXT NOT NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz,
            deleted_at timestamptz
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pokemons (
            id uuid PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            "order" integer NOT NULL,
            status statusenum NOT NULL,
            external_image TEXT NOT NULL,
            hp integer,
            image TEXT,
            speed integer,
            height integer,
            weight integer,
            attack integer,
            defense integer,
            habitat TEXT,
            is_baby boolean,
            shape_url TEXT,
            shape_name TEXT,
            is_mythical boolean,
            gender_rate integer,
            is_legendary boolean,
            capture_rate integer,
            hatch_counter integer,
            base_happiness integer,
            special_attack integer,
            base_experience integer,
            special_defense integer,
            evolution_chain TEXT,
            evolves_from_species TEXT,
            has_gender_differences boolean,
            growth_rate_id uuid REFERENCES pokemon_growth_rates(id),
            created_at timestamptz NOT NULL,
            updated_at timestamptz,
            deleted_at timestamptz
        );
        """
    )

    op.create_table(
        'pokemon_pokemon_moves',
        sa.Column('pokemon_id', sa.Uuid(), sa.ForeignKey('pokemons.id'), primary_key=True),
        sa.Column(
            'pokemon_move_id',
            sa.Uuid(),
            sa.ForeignKey('pokemon_moves.id'),
            primary_key=True,
        ),
    )

    op.create_table(
        'pokemon_pokemon_abilities',
        sa.Column('pokemon_id', sa.Uuid(), sa.ForeignKey('pokemons.id'), primary_key=True),
        sa.Column(
            'pokemon_ability_id',
            sa.Uuid(),
            sa.ForeignKey('pokemon_abilities.id'),
            primary_key=True,
        ),
    )

    op.create_table(
        'pokemon_pokemon_types',
        sa.Column('pokemon_id', sa.Uuid(), sa.ForeignKey('pokemons.id'), primary_key=True),
        sa.Column(
            'pokemon_type_id',
            sa.Uuid(),
            sa.ForeignKey('pokemon_types.id'),
            primary_key=True,
        ),
    )

    op.create_table(
        'pokemon_type_weaknesses',
        sa.Column('type_id', sa.Uuid(), sa.ForeignKey('pokemon_types.id'), primary_key=True),
        sa.Column(
            'weak_against_id',
            sa.Uuid(),
            sa.ForeignKey('pokemon_types.id'),
            primary_key=True,
        ),
    )

    op.create_table(
        'pokemon_type_strengths',
        sa.Column('type_id', sa.Uuid(), sa.ForeignKey('pokemon_types.id'), primary_key=True),
        sa.Column(
            'strong_against_id',
            sa.Uuid(),
            sa.ForeignKey('pokemon_types.id'),
            primary_key=True,
        ),
    )

    op.create_table(
        'pokemon_evolutions',
        sa.Column('pokemon_id', sa.Uuid(), sa.ForeignKey('pokemons.id'), primary_key=True),
        sa.Column(
            'evolution_id',
            sa.Uuid(),
            sa.ForeignKey('pokemons.id'),
            primary_key=True,
        ),
    )


def downgrade() -> None:
    op.drop_table('pokemon_evolutions')
    op.drop_table('pokemon_type_strengths')
    op.drop_table('pokemon_type_weaknesses')
    op.drop_table('pokemon_pokemon_types')
    op.drop_table('pokemon_pokemon_abilities')
    op.drop_table('pokemon_pokemon_moves')
    op.drop_table('pokemons')
    op.drop_table('pokemon_types')
    op.drop_table('pokemon_abilities')
    op.drop_table('pokemon_moves')
    op.drop_table('pokemon_growth_rates')
