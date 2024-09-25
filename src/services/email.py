from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from .auth import auth_service
from .environment import environment


async def send(address: EmailStr, subject: str, host: str, type: str) -> None:
    TOKEN = await auth_service.create_token(address, expire=True)

    config = ConnectionConfig(
        MAIL_FROM_NAME='Contacts API',
        TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
        **environment('FASTAPIMAIL', True),
    )

    try:
        message = MessageSchema(
            subject=subject,
            recipients=[address],
            template_body={'url': f'{host}api/auth/{type}/{TOKEN}'},
            subtype=MessageType.html,
        )

        await FastMail(config).send_message(message, f'{type}-email.html')
    except ConnectionErrors as err:
        print(err)
