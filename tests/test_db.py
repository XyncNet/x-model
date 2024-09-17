from asyncio import run
from os import getenv as env
from dotenv import load_dotenv
from tortoise.backends.asyncpg import AsyncpgDBClient

from tortoise_api_model import init_db, model

load_dotenv()


def test_init_db():
    assert isinstance(run(init_db(env("DB_URL"), model)), AsyncpgDBClient), "DB corrupt"
