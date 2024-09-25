from fastapi import Depends, HTTPException, status
from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, \
    async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .services.environment import environment


engine: AsyncEngine = None


async def init_engine() -> None:
    global engine

    try:
        engine = create_async_engine(environment())

        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
    except OperationalError as err:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            'Database connection failed: ' + str(err),
        )
    except SQLAlchemyError as err:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(err))


async def init_db_once() -> None:
    if not init_db_once.done:
        await init_engine()
        await init_db()

        init_db_once.done = True


init_db_once.done = False


async def get_db(db_init=Depends(init_db_once)):
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
        autocommit=False,
    )

    try:
        async with async_session() as session:
            yield session
    except OperationalError as err:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            'Database connection failed: ' + str(err),
        )


class Base(DeclarativeBase):
    ...


class Contact(Base):
    __tablename__ = 'contacts'

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(30), index=True)

    last_name: Mapped[str] = mapped_column(
        String(40),
        index=True,
        nullable=True,
    )

    email: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True)
    birthday: Mapped[str] = mapped_column(Date(), nullable=True)
    bio: Mapped[str] = mapped_column(String(400), nullable=True)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('users.id'),
        nullable=True,
    )

    user: Mapped['User'] = relationship(
        'User',
        backref='contacts',
        lazy='joined',
    )


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )

    password: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(255), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean(), default=False)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)


async def init_db():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except SQLAlchemyError as err:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            'Database initialization failed: ' + str(err),
        )
