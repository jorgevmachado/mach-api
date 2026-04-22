from __future__ import annotations

from http import HTTPStatus

from fastapi import HTTPException

from app.core.exceptions import handle_service_exception
from app.core.security import create_access_token, get_password_hash, verify_password
from app.domain.auth.repository import UserRepository
from app.domain.auth.schema import LoginRequest, RegisterRequest
from app.models.enums import StatusEnum
from app.models.user import User


class AuthService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def register(self, data: RegisterRequest) -> User:
        try:
            existing_email = await self.repository.get_by_email(data.email)
            if existing_email:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail='Email already registered',
                )

            existing_username = await self.repository.get_by_username(data.username)
            if existing_username:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail='Username already taken',
                )

            user_data = data.model_dump()
            user_data['password'] = get_password_hash(data.password)
            user_data['status'] = StatusEnum.INCOMPLETE

            return await self.repository.create(user_data)

        except Exception as exception:
            handle_service_exception(
                exception,
                logger=__import__('logging').getLogger(__name__),
                service='AuthService',
                operation='register',
                raise_exception=True,
            )

    async def login(self, data: LoginRequest) -> dict:
        try:
            user = await self.repository.get_by_email_or_username(data.credential)

            if not user:
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail='Invalid credentials',
                )

            if not verify_password(data.password, user.password):
                await self.repository.update_auth_failure(user.id)
                raise HTTPException(
                    status_code=HTTPStatus.UNAUTHORIZED,
                    detail='Invalid credentials',
                )

            await self.repository.update_auth_success(user.id)
            token = create_access_token({'sub': str(user.id)})

            return {'access_token': token, 'token_type': 'bearer'}

        except Exception as exception:
            handle_service_exception(
                exception,
                logger=__import__('logging').getLogger(__name__),
                service='AuthService',
                operation='login',
                raise_exception=True,
            )
