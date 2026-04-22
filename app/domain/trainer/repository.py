from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.core.repository.base import BaseRepository
from app.models.trainer import Trainer


class TrainerRepository(BaseRepository[Trainer]):
    model = Trainer

    async def get_by_user_id(self, user_id: UUID) -> Trainer | None:
        return await self.session.scalar(
            select(Trainer).where(Trainer.user_id == user_id)
        )

    async def create(self, data: dict) -> Trainer:
        trainer = Trainer(**data)
        return await self.save(trainer)
