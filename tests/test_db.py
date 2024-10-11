from asyncio import run
from os import getenv as env
from dotenv import load_dotenv
from tortoise.backends.asyncpg import AsyncpgDBClient

from tortoise_api_model import init_db, model

load_dotenv()

PG_DSN = f"postgres://{env('POSTGRES_USER')}:{env('POSTGRES_PASSWORD')}@{env('POSTGRES_HOST', 'xyncdbs')}:{env('POSTGRES_PORT', 5432)}/{env('POSTGRES_DB', env('POSTGRES_USER'))}"


def test_init_db():
    assert isinstance(run(init_db(PG_DSN, model)), AsyncpgDBClient), "DB corrupt"
