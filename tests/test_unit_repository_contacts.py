from datetime import date
from unittest import IsolatedAsyncioTestCase, main
from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import User
from src.schemas.contact import Request
from src.repository.contacts import create


class TestContacts(IsolatedAsyncioTestCase):
    async def test_create(self) -> None:
        FIELDS = {
            'first_name': 'Jack',
            'last_name': 'Jones',
            'email': 'j.jones@post.com',
            'phone_number': '+123456789012',
            'birthday': date(2002, 3, 15),
            'bio': 'Bla bla bla bla bla bla bla bla bla bla',
        }

        body = Request(**FIELDS)

        result = await create(AsyncMock(spec=AsyncSession), User(id=1), body)

        for field in FIELDS.keys():
            self.assertEqual(getattr(result, field), getattr(body, field))

        self.assertTrue(hasattr(result, 'id'))


if __name__ == '__main__':
    main()
