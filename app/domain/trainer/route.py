from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import get_current_user
from app.domain.auth.repository import UserRepository
from app.domain.trainer.repository import TrainerRepository
from app.domain.trainer.schema import InitializeTrainerRequest, InitializeTrainerResponse
from app.domain.trainer.service import TrainerService
from app.models.user import User

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def get_trainer_service(session: Session) -> TrainerService:
    return TrainerService(TrainerRepository(session), UserRepository(session))


@router.post('/initialize', response_model=InitializeTrainerResponse, status_code=HTTPStatus.CREATED)
async def initialize_trainer(
    data: InitializeTrainerRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[TrainerService, Depends(get_trainer_service)],
):
    trainer = await service.initialize(current_user.id, data)
    return trainer
