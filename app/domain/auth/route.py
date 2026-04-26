from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.database import get_session
from app.core.security import get_current_user
from app.domain.auth.repository import UserRepository
from app.domain.auth.schema import (
    AuthMeSchema,
    LoginResultSchema,
    LoginSchema,
    RegisterResultSchema,
    RegisterSchema,
)
from app.domain.auth.service import AuthService
from app.domain.trainer.repository import TrainerRepository
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

Session = Annotated[AsyncSession, Depends(get_session)]


def get_auth_service(session: Session) -> AuthService:
    return AuthService(UserRepository(session), TrainerRepository(session))


@router.post('/register', response_model=RegisterResultSchema, status_code=HTTPStatus.CREATED)
async def register(
    data: RegisterSchema,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    user = await service.register(data)
    return user


@router.post('/login', response_model=LoginResultSchema, status_code=HTTPStatus.OK)
async def login(
    data: LoginSchema,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.login(data)


@router.get('/me', response_model=AuthMeSchema, status_code=HTTPStatus.OK)
async def me(
    current_user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return await service.me(current_user)
