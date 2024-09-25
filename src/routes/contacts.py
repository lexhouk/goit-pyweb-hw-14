from fastapi import APIRouter, Depends, Path, Query, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, User
from src.repository.contacts import birthday, create, delete, get, read, update
from src.schemas.contact import Request, Response, Responses
from src.services.auth import auth_service


router = APIRouter(
    prefix='/contacts',
    tags=['Contacts'],
    dependencies=[Depends(RateLimiter(3, minutes=1))],
)


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_contact(
    body: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
) -> Response:
    return await create(db, user, body)


@router.get('/')
async def read_contacts(
    first_name: str = None,
    last_name: str = None,
    email: str = Query(None, pattern=r'^[^@]+@[^\.]+\.\w+$'),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
) -> Responses:
    return await read(db, user, first_name, last_name, email)


@router.get('/birthdays')
async def read_birthday_contacts(
    days: int = Query(default=7, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
) -> Responses:
    return await birthday(db, user, days)


@router.get('/{contact_id}')
async def read_contact(
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
) -> Response:
    return await get(db, user, contact_id)


@router.put('/{contact_id}')
async def update_contact(
    body: Request,
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
) -> Response:
    return await update(db, user, body, contact_id)


@router.delete('/{contact_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    contact_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(auth_service.get_current_user)
) -> None:
    await delete(db, user, contact_id)
