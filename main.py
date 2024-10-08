from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from redis.asyncio import Redis as InitRedis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from uvicorn import run

from src.database import get_db
from src.routes.auth import router as auth_router
from src.routes.contacts import router as contacts_router
from src.routes.users import router as users_router
from src.services.environment import environment


@asynccontextmanager
async def launch(app: FastAPI):
    '''
    Connecting the cache to the system for determining limits on the number of requests.

    :param app: Application object.
    :type app: FastAPI
    '''

    cache = await InitRedis(
        **environment('REDIS', True, True),
        db=0,
        encoding='utf-8',
        decode_responses=True,
    )

    await FastAPILimiter.init(cache)

    yield


app = FastAPI(lifespan=launch)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    **{f'allow_{name}s': ['*'] for name in ('origin', 'method', 'header')},
)

app.include_router(auth_router, prefix='/api')
app.include_router(contacts_router, prefix='/api')
app.include_router(users_router, prefix='/api')


@app.get('/api/healthchecker', tags=['Status'])
async def root(db: AsyncSession = Depends(get_db)) -> dict:
    '''
    Endpoint for determining application readiness.

    :param db: Database connection.
    :type db: AsyncSession
    :return: Welcome message when ready. Otherwise, an error message is
        displayed.
    :rtype: dict

    :raises HTTPException: If the connection to the database failed due to
        invalid accesses being provided or for some other reason (for example,
        the server is not running).
    '''

    try:
        if not await db.execute(text('SELECT 1')):
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                'Database is not configured correctly',
            )

        return {'message': 'Welcome to FastAPI!'}
    except Exception as err:
        print(err)

        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            'Error connecting to the database',
        )


if __name__ == '__main__':
    run('main:app', host='0.0.0.0', port=8000, reload=True)
