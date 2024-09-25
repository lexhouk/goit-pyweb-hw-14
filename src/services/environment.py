from os import environ

from dotenv import load_dotenv


def environment(
    name: str = 'POSTGRES_URL',
    prefix: bool = False,
    lower: bool = False
) -> dict | str:
    load_dotenv()

    if prefix:
        name += '_'

        return {
            (key[len(name):].lower() if lower else key[len(name):]): value
            for key, value in environ.items()
            if key.startswith(name) and key != f'{name}TAG'
        }

    return environ[name]
