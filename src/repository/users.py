from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, User
from src.schemas.user import Response, TokenSchema, UserRequest
from src.services.auth import auth_service, Token


async def create(
    body: UserRequest,
    db: AsyncSession = Depends(get_db)
) -> Response:
    '''
    Create a new user based on the provided email address and password.

    :param body: A couple of fields are required to create an entity.
    :type body: UserRequest
    :param db: Database connection.
    :type db: AsyncSession
    :return: The part of the created entity that contains the ID and email address.
    :rtype: Response
    '''

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
    '''
    Making changes to one or more fields of an existing user.

    :param user: A set of all fields from the user model for the database.
    :type user: User
    :param db: Database connection.
    :type db: AsyncSession
    :param revoke: Indication that the refresh token must be reset.
    :type revoke: bool
    :return: The access and update token and their type if the entity was successfully updated.
    :rtype: TokenSchema | None
    '''

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
    '''
    The process of marking a user as one whose email address has been verified.

    :param email: Email address of an existing user.
    :type email: str
    :param db: Database connection.
    :type db: AsyncSession
    '''

    if (user := await auth_service.get_user_by_email(email, db)):
        user.verified = True

        await db.commit()


async def avatar(email: str, url: str, db: AsyncSession) -> Response:
    '''
    Setting a link to a user's avatar.

    :param email: The e-mail address of the user whose avatar needs to be specified.
    :type email: str
    :param url: The web address of the image that represents the user's image.
    :type url: str
    :param db: Database connection.
    :type db: AsyncSession
    :return: The entity of a particular user if the user was successfully found at the specified email address.
    :rtype: Response
    '''

    if (user := await auth_service.get_user_by_email(email, db)):
        user.avatar = url

        await db.commit()

        return user
