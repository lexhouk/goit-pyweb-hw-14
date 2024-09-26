from datetime import date
from typing import Any
from unittest import IsolatedAsyncioTestCase, main
from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Contact, User
from src.schemas.contact import Request
from src.repository.contacts import birthday, create, delete, read, update


class TestContacts(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user = User(id=1)

    def setUp(self) -> None:
        self.__db = AsyncMock(AsyncSession)

    async def __compare(
        self,
        result: Any,
        fields: dict,
        body: Request
    ) -> None:
        self.assertIsInstance(result, Contact)

        for field in fields.keys():
            self.assertEqual(getattr(result, field), getattr(body, field))

    async def __create(self, fields: dict) -> None:
        body = Request(**fields)

        result = await create(self.__db, self.user, body)

        await self.__compare(result, fields, body)

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

    async def test_read_any(self) -> None:
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

    async def test_read_absent(self) -> None:
        contacts = []

        mocked_contacts = Mock()
        mocked_contacts.scalars.return_value.all.return_value = contacts

        self.__db.execute.return_value = mocked_contacts

        with self.assertRaises(HTTPException):
            await read(self.__db, self.user)

    @patch('datetime.date.today', wraps=date)
    async def _test_birthday(self, mock_date) -> None:
        contacts = [
            Contact(
                first_name='Jack',
                email='jack@post.com',
                birthday=date(2000, 5, 3),
            ),
            Contact(
                first_name='Bart',
                email='bart@post.com',
                birthday=date(2005, 9, 30),
            ),
        ]

        mocked_contacts = Mock()
        mocked_contacts.scalars.return_value.all.return_value = contacts

        self.__db.execute.return_value = mocked_contacts

        mock_date.today.return_value = date(2024, 9, 26)

        result = await birthday(self.__db, self.user, 7)

        self.assertEqual(result, [contacts[1]])

    async def test_update(self) -> None:
        FIELDS = {'first_name': 'Jack', 'email': 'jack@post.com'}
        body = Request(**FIELDS)

        contact = Contact(id=2, **FIELDS)

        mocked_contact = Mock()
        mocked_contact.scalar_one_or_none.return_value = contact

        self.__db.execute.return_value = mocked_contact

        result = await update(self.__db, self.user, body, contact.id)

        await self.__compare(result, FIELDS, body)

    async def test_delete(self) -> None:
        contact = Contact(id=2, first_name='Jack', email='jack@post.com')

        mocked_contact = Mock()
        mocked_contact.scalar_one_or_none.return_value = contact

        self.__db.execute.return_value = mocked_contact

        await delete(self.__db, self.user, contact.id)

        self.__db.delete.assert_called_once_with(contact)
        self.__db.commit.assert_called_once()


if __name__ == '__main__':
    main()
