from fastapi.testclient import TestClient
from pytest import fixture
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from main import app
from src.database import get_db

engine = create_async_engine(
    'sqlite+aiosqlite:///:memory:',
    connect_args={'check_same_thread': False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    engine,
    **{key: False for key in ('autocommit', 'autoflush', 'expire_on_commit')},
)


@fixture(scope='module')
def client():
    async def override_get_db():
        session = TestingSessionLocal()

        try:
            yield session
        except Exception as err:
            print(err)

            await session.rollback()
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)
