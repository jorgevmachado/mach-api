from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import selectinload

from app.core.repository.base import BaseRepository
from app.models.enums import PokedexStatusEnum
from app.models.my_pokemon import MyPokemon
from app.models.pokedex import Pokedex
from app.models.pokemon import Pokemon
from app.models.trainer import Trainer


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TrainerRepository(BaseRepository[Trainer]):
    model = Trainer
    relations = (
        selectinload(Trainer.pokedex_entries)
        .selectinload(Pokedex.pokemon)
        .selectinload(Pokemon.types),
        selectinload(Trainer.my_pokemons)
        .selectinload(MyPokemon.pokemon)
        .selectinload(Pokemon.types),
    )

    async def get_by_user_id(self, user_id: UUID) -> Trainer | None:
        return await self.find_by(user_id=user_id)

    async def get_by_id(self, trainer_id: UUID) -> Trainer | None:
        return await self.find_by(id=trainer_id)

    async def create(self, data: dict) -> Trainer:
        trainer = Trainer(**data)
        return await self.save(trainer)

    async def update_pokedex_status(
        self,
        trainer_id: UUID,
        status: PokedexStatusEnum,
    ) -> None:
        await self.session.execute(
            update(Trainer)
            .where(Trainer.id == trainer_id)
            .values(
                pokedex_status=status,
                updated_at=_utcnow(),
            )
        )
        await self.session.commit()
