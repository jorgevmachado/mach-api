from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.domain.trainer.schema import TrainerMeSchema
from app.models.enums import GenderEnum, StatusEnum


class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    username: str
    gender: GenderEnum
    date_of_birth: datetime
    password: str

    @field_validator('password')
    @classmethod
    def password_min_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters')
        return value


class RegisterResultSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    username: str
    status: StatusEnum
    created_at: datetime


class LoginSchema(BaseModel):
    credential: str
    password: str


class LoginResultSchema(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class AuthMeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    trainer: TrainerMeSchema | None = None
    username: str
    status: StatusEnum
    created_at: datetime
