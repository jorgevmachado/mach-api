from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import GenderEnum, StatusEnum
from app.domain.trainer.schema import TrainerMeResponse

class RegisterRequest(BaseModel):
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


class RegisterResponse(BaseModel):
    id: UUID
    name: str
    email: str
    username: str
    status: StatusEnum
    created_at: datetime

    model_config = {'from_attributes': True}


class LoginRequest(BaseModel):
    credential: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class MeResponse(BaseModel):
    id: UUID
    name: str
    email: str
    trainer: TrainerMeResponse | None = None
    username: str
    status: StatusEnum
    created_at: datetime

    model_config = {'from_attributes': True}
