# Contacts API

## Deployment

```bash
$ git clone https://github.com/lexhouk/goit-pyweb-hw-13-task-1.git
$ cd goit-pyweb-hw-13-task-1
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
