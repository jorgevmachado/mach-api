from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class InitializeTrainerRequest(BaseModel):
    pokeballs: int
    capture_rate: int


class InitializeTrainerResponse(BaseModel):
    id: UUID
    user_id: UUID
    pokeballs: int
    capture_rate: int
    created_at: datetime

    model_config = {'from_attributes': True}
