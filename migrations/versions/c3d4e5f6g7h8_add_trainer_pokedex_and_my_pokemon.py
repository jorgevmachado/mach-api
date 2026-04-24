"""add trainer pokedex and my pokemon

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-04-24 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE pokedexstatusenum AS ENUM ('EMPTY', 'INITIALIZING', 'READY', 'FAILED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )

    op.execute(
        """
        ALTER TABLE trainers
        ADD COLUMN IF NOT EXISTS pokedex_status pokedexstatusenum NOT NULL DEFAULT 'EMPTY';
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS pokedex (
            id uuid PRIMARY KEY,
            hp integer NOT NULL,
            max_hp integer NOT NULL,
            speed integer NOT NULL,
            attack integer NOT NULL,
            defense integer NOT NULL,
            special_attack integer NOT NULL,
            special_defense integer NOT NULL,
            formula TEXT NOT NULL,
            pokemon_id uuid NOT NULL REFERENCES pokemons(id),
            trainer_id uuid NOT NULL REFERENCES trainers(id),
            iv_hp integer NOT NULL,
            ev_hp integer NOT NULL,
            wins integer NOT NULL,
            level integer NOT NULL,
            losses integer NOT NULL,
            battles integer NOT NULL,
            iv_speed integer NOT NULL,
            ev_speed integer NOT NULL,
            iv_attack integer NOT NULL,
            ev_attack integer NOT NULL,
            iv_defense integer NOT NULL,
            ev_defense integer NOT NULL,
            experience integer NOT NULL,
            iv_special_attack integer NOT NULL,
            ev_special_attack integer NOT NULL,
            iv_special_defense integer NOT NULL,
            ev_special_defense integer NOT NULL,
            discovered boolean NOT NULL DEFAULT false,
            discovered_at timestamptz,
            created_at timestamptz NOT NULL,
            updated_at timestamptz,
            deleted_at timestamptz,
            CONSTRAINT uq_pokedex_trainer_pokemon UNIQUE (trainer_id, pokemon_id)
        );
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS my_pokemons (
            id uuid PRIMARY KEY,
            hp integer NOT NULL,
            max_hp integer NOT NULL,
            nickname TEXT NOT NULL,
            speed integer NOT NULL,
            attack integer NOT NULL,
            defense integer NOT NULL,
            special_attack integer NOT NULL,
            special_defense integer NOT NULL,
            formula TEXT NOT NULL,
            pokemon_id uuid NOT NULL REFERENCES pokemons(id),
            trainer_id uuid NOT NULL REFERENCES trainers(id),
            iv_hp integer NOT NULL,
            ev_hp integer NOT NULL,
            wins integer NOT NULL,
            level integer NOT NULL,
            losses integer NOT NULL,
            battles integer NOT NULL,
            iv_speed integer NOT NULL,
            ev_speed integer NOT NULL,
            iv_attack integer NOT NULL,
            ev_attack integer NOT NULL,
            iv_defense integer NOT NULL,
            ev_defense integer NOT NULL,
            experience integer NOT NULL,
            iv_special_attack integer NOT NULL,
            ev_special_attack integer NOT NULL,
            iv_special_defense integer NOT NULL,
            ev_special_defense integer NOT NULL,
            captured_at timestamptz NOT NULL,
            created_at timestamptz NOT NULL,
            updated_at timestamptz,
            deleted_at timestamptz
        );
        """
    )

    op.create_table(
        'my_pokemon_pokemon_moves',
        sa.Column('my_pokemon_id', sa.Uuid(), sa.ForeignKey('my_pokemons.id'), primary_key=True),
        sa.Column('pokemon_move_id', sa.Uuid(), sa.ForeignKey('pokemon_moves.id'), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table('my_pokemon_pokemon_moves')
    op.drop_table('my_pokemons')
    op.drop_table('pokedex')
    op.execute("ALTER TABLE trainers DROP COLUMN IF EXISTS pokedex_status;")
    op.execute("DROP TYPE IF EXISTS pokedexstatusenum;")
