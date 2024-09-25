from cloudinary import CloudinaryImage, config
from cloudinary.uploader import upload
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db, User
from src.repository.users import avatar
from src.schemas.user import Response
from src.services.auth import auth_service
from src.services.environment import environment


router = APIRouter(prefix='/users', tags=['Users'])


@router.patch('/')
async def set_avatar(
    file: UploadFile = File(),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Response:
    config(secure=True, **environment('CLOUDINARY', True, True))

    identifier = f'ContactApp/{current_user.id}'

    source = upload(file.file, public_id=identifier, overwrite=True)

    url = CloudinaryImage(identifier).build_url(
        width=128,
        height=128,
        crop='fill',
        version=source.get('version'),
    )

    return await avatar(current_user.email, url, db)
