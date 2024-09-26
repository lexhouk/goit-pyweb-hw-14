from os import environ

from dotenv import load_dotenv


def environment(
    name: str = 'POSTGRES_URL',
    prefix: bool = False,
    lower: bool = False
) -> dict | str:
    '''
    Reads environment variables.

    :param name: The full name of the environment variable or its beginning.
    :type name: str
    :param prefix: Indicates that the previous parameter is only part of the
        variable.
    :type prefix: bool
    :param lower: Specifies that the result keys should be written in lowercase
        letters.
    :type lower: bool
    :return: A set of environment variable values ​​if prefixed or a single
        environment variable is provided.
    :rtype: dict | str
    '''

    load_dotenv()

    if prefix:
        name += '_'

        return {
            (key[len(name):].lower() if lower else key[len(name):]): value
            for key, value in environ.items()
            if key.startswith(name) and key != f'{name}TAG'
        }

    return environ[name]
