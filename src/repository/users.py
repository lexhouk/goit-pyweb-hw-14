from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, User
from src.schemas.user import Response, TokenSchema, UserRequest
from src.services.auth import auth_service, Token


async def create(
    body: UserRequest,
    db: AsyncSession = Depends(get_db)
) -> Response:
    user = User(email=body.username, password=body.password)

    db.add(user)

    await db.commit()
    await db.refresh(user)

    return user


async def update(
    user: User,
    db: AsyncSession,
    revoke: bool = False
) -> TokenSchema | None:
    if revoke:
        user.token = None
    else:
        result = {
            **{
                token.value: await auth_service.create_token(user.email, token)
                for token in Token
            },
            'token_type': 'bearer',
        }

        user.token = result[Token.REFRESH.value]

    await db.commit()

    return result or None


async def verify(email: str, db: AsyncSession) -> None:
    if (user := await auth_service.get_user_by_email(email, db)):
        user.verified = True

        await db.commit()


async def avatar(email: str, url: str, db: AsyncSession) -> Response:
    if (user := await auth_service.get_user_by_email(email, db)):
        user.avatar = url

        await db.commit()

        return user
