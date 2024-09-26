# Contacts API

## Development

```bash
$ sphinx-quickstart docs
$ python -m pip freeze > requirements.txt
$ docker compose up -d
$ docker exec -it lexhouk-hw-14-documentation make -C docs html
$ cd docs/_build/html
$ python -m http.server
```

Go to http://localhost:8000.

## Deployment

```bash
$ git clone https://github.com/lexhouk/goit-pyweb-hw-14.git
$ cd goit-pyweb-hw-14
$ poetry install
$ docker compose up -d
$ alembic upgrade head
```

## Usage

```bash
$ docker compose up -d
$ poetry shell
$ python main.py
```

All available endoints can be viewed in [Swagger UI](http://localhost:8000/docs)
or [ReDoc](http://localhost:8000/redoc), and can only be tested in the former.
