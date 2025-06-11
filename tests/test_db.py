from asyncio import run
from os import getenv as env
from dotenv import load_dotenv
from tortoise.backends.asyncpg import AsyncpgDBClient

from x_model import init_db, models

load_dotenv()

PG_DSN = f"postgres://{env('POSTGRES_USER')}:{env('POSTGRES_PASSWORD')}@{env('POSTGRES_HOST', 'xyncdbs')}:{env('POSTGRES_PORT', 5432)}/{env('POSTGRES_DB', env('POSTGRES_USER'))}"

TORM = {
    "connections": {"default": PG_DSN},
    "apps": {"models": {"models": [models]}},
    "use_tz": False,
    "timezone": "UTC",
}


def test_init_db():
    assert isinstance(run(init_db(TORM)), AsyncpgDBClient), "DB corrupt"
