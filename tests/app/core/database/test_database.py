import pytest
from sqlalchemy import select

from app.models.trainer import Trainer
from app.shared.enums.gender_enum import GenderEnum
from app.shared.enums.role_enum import RoleEnum
from app.shared.enums.status_enum import StatusEnum


@pytest.mark.asyncio
async def test_create_user_db(session, mock_db_time):
    total = 0
    pokeballs = 5
    capture_rate = 45
    with mock_db_time(model=Trainer) as time:
        new_user = Trainer(
            role=RoleEnum.USER,
            name='john Doe',
            email='john@doe.com',
            gender=GenderEnum.MALE,
            status=StatusEnum.ACTIVE,
            password='secret',
            pokeballs=pokeballs,
            capture_rate=capture_rate,
            date_of_birth='1990-07-20',
            total_authentications=total,
            authentication_success=total,
            authentication_failures=total,
        )
        session.add(new_user)
        await session.commit()

    user = await session.scalar(select(Trainer).where(Trainer.email == 'john@doe.com'))
    assert user.name == 'john Doe'
    assert user.email == 'john@doe.com'
    assert user.gender == GenderEnum.MALE
    assert user.status == StatusEnum.ACTIVE
    assert user.total_authentications == total
    assert user.authentication_success == total
    assert user.authentication_failures == total
    assert user.pokeballs == pokeballs
    assert user.capture_rate == capture_rate
    assert user.created_at == time
    assert user.updated_at == time
