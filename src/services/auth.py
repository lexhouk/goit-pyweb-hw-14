from enum import Enum
from datetime import datetime, timedelta, UTC
from pickle import dumps, loads

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, User
from src.schemas.user import Response
from .environment import environment


class Token(Enum):
    ACCESS = 'access_token'
    REFRESH = 'refresh_token'


class Auth:
    __pwd_context = CryptContext(['bcrypt'], deprecated='auto')

    def __init__(self) -> None:
        '''
        Setting the encryption algorithm and secret key for the JWT token. A
        connection to the caching service is also made to save data about the
        current user.
        '''

        self.__ALGORITHM = environment('JWT_ALGORITHM')
        self.__SECRET = environment('JWT_SECRET')

        self.__cache = Redis(
            **environment('REDIS', True, True),
            db=0,
            encoding='utf-8',
            decode_responses=True,
        )

    def verify_password(
        self,
        plain_password: str,
        hashed_password: str
    ) -> bool:
        '''
        Checking the correctness of the password.

        :param plain_password: Password in the form in which it was entered by
            the user.
        :type plain_password: str
        :param hashed_password: Password as it is stored in the database.
        :type hashed_password: str
        :return: True if the values ​​passed through the parameters are the same
            password.
        :rtype: bool
        '''

        return self.__pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return self.__pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer('api/auth/login')

    async def create_token(
        self,
        email: str,
        token: Token = None,
        expire: bool = False
    ) -> str:
        '''
        Generation of one of the types of tokens where the e-mail address,
        creation date and expiration date are used as the payload.

        :param email: The email address used as part of the payload.
        :type email: str
        :param token: One of two common types of tokens (access token and
            refresh token) or an empty value for a non-standard token.
        :type token: Token
        :param expire: True value for specifying the token's validity period in
            days, otherwise in minutes.
        :type expire: bool
        :return: A string representation of the generated token.
        :rtype: str
        '''

        payload = {
            'sub': email,
            **{key: datetime.now(UTC) for key in ('iat', 'exp')},
        }

        if token:
            payload['scope'] = token.value

        payload['exp'] += timedelta(days=7) if expire \
            else timedelta(minutes=15)

        return jwt.encode(payload, self.__SECRET, self.__ALGORITHM)

    async def decode_token(self, token: str, type: Token = None) -> str:
        '''
        Extract the email address from the token string representation payload.

        :param token: The token from which you need to get information.
        :type token: str
        :param token: One of two common types of tokens (access token and
            refresh token) or an empty value for a non-standard token.
        :type token: Token
        :return: The email address is extracted from the token.
        :rtype: str

        :raises HTTPException: If the token cannot be decoded with an incorrect
            structure or when the type of token specified in the payload is
            incorrect.
        '''

        try:
            payload = jwt.decode(token, self.__SECRET, [self.__ALGORITHM])

            if not type or payload['scope'] == type.value:
                return payload['sub']

            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                'Invalid scope for token',
            )
        except JWTError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                'Invalid token',
            )

    async def get_user_by_email(
        self,
        email: str,
        db: AsyncSession = Depends(get_db)
    ) -> Response | None:
        '''
        Get a model's entity based on its email address.

        :param email: The e-mail address of the owner of which you need to
            find.
        :type email: str
        :param db: Database connection.
        :type db: AsyncSession
        :return: The user entity, if one exists, with the specified email
            address.
        :rtype: Response | None
        '''

        user = await db.execute(select(User).where(User.email == email))

        return user.scalar_one_or_none()

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ) -> Response:
        '''
        Get the logged in user.

        :param token: The access token by which the user is searched.
        :type token: str
        :param db: Database connection.
        :type db: AsyncSession
        :return: The entity of the found user.
        :rtype: Response

        :raises HTTPException: If the token type does not match or the user
            with the email address contained in the token does not exist.
        '''

        credentials_exception = HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            'Could not validate credentials',
            {'WWW-Authenticate': 'Bearer'},
        )

        try:
            payload = jwt.decode(token, self.__SECRET, [self.__ALGORITHM])

            if payload['scope'] != Token.ACCESS.value or not payload['sub']:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        if (user := self.__cache.get(name := f"user:{payload['sub']}")):
            user = loads(user)
        else:
            if not (user := await self.get_user_by_email(payload['sub'], db)):
                raise credentials_exception

            self.__cache.set(name, dumps(user))
            self.__cache.expire(name, 3600)  # 1 hour

        return user


auth_service = Auth()
