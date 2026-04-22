from __future__ import annotations

from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException

from app.core.exceptions import handle_service_exception
from app.domain.auth.repository import UserRepository
from app.domain.trainer.repository import TrainerRepository
from app.domain.trainer.schema import InitializeTrainerRequest
from app.models.enums import StatusEnum
from app.models.trainer import Trainer


class TrainerService:
    def __init__(
        self,
        trainer_repository: TrainerRepository,
        user_repository: UserRepository,
    ) -> None:
        self.trainer_repository = trainer_repository
        self.user_repository = user_repository

    async def initialize(self, user_id: UUID, data: InitializeTrainerRequest) -> Trainer:
        try:
            existing = await self.trainer_repository.get_by_user_id(user_id)
            if existing:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail='Trainer already initialized',
                )

            trainer = await self.trainer_repository.create(
                {
                    'user_id': user_id,
                    'pokeballs': data.pokeballs,
                    'capture_rate': data.capture_rate,
                }
            )

            await self.user_repository.update_status(user_id, StatusEnum.COMPLETE)

            return trainer

        except Exception as exception:
            handle_service_exception(
                exception,
                logger=__import__('logging').getLogger(__name__),
                service='TrainerService',
                operation='initialize',
                raise_exception=True,
            )
