from datetime import date
from unittest import IsolatedAsyncioTestCase, main
from unittest.mock import AsyncMock, Mock

from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Contact, User
from src.schemas.contact import Request
from src.repository.contacts import create, read


class TestContacts(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user = User(id=1)

    def setUp(self) -> None:
        self.__db = AsyncMock(AsyncSession)

    async def __create(self, fields: dict) -> None:
        body = Request(**fields)

        result = await create(self.__db, self.user, body)

        self.assertIsInstance(result, Contact)

        for field in fields.keys():
            self.assertEqual(getattr(result, field), getattr(body, field))

        self.assertTrue(hasattr(result, 'id'))

    async def test_create_full(self) -> None:
        await self.__create({
            'first_name': 'Jack',
            'last_name': 'Jones',
            'email': 'j.jones@post.com',
            'phone_number': '+123456789012',
            'birthday': date(2002, 3, 15),
            'bio': 'Bla bla bla bla bla bla bla bla bla bla',
        })

    async def test_create_required(self) -> None:
        await self.__create({
            'first_name': 'Jack',
            'email': 'jack@post.com',
        })

    async def test_create_missed(self) -> None:
        with self.assertRaises(ValidationError):
            await self.__create({'first_name': 'Jack'})

    async def test_create_incorrect(self) -> None:
        with self.assertRaises(ValidationError):
            await self.__create({
                'first_name': 'Jack',
                'email': 'jack',
            })

    async def test_read(self) -> None:
        contacts = [
            Contact(
                first_name=f'Jack {generation}',
                email=f'jack{generation}@post.com',
            )
            for generation in range(3)
        ]

        mocked_contacts = Mock()
        mocked_contacts.scalars.return_value.all.return_value = contacts

        self.__db.execute.return_value = mocked_contacts

        result = await read(self.__db, self.user)

        self.assertEqual(result, contacts)


if __name__ == '__main__':
    main()
