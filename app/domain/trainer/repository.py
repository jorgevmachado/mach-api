from __future__ import annotations

from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import selectinload

from app.core.repository.base import BaseRepository
from app.models.enums import PokedexStatusEnum
from app.models.trainer import Trainer


class TrainerRepository(BaseRepository[Trainer]):
    model = Trainer
    relations = (
        selectinload(Trainer.pokedex_entries),
        selectinload(Trainer.my_pokemons),
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
            .values(pokedex_status=status)
        )
        await self.session.commit()
