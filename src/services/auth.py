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
        user = await db.execute(select(User).where(User.email == email))

        return user.scalar_one_or_none()

    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ):
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
