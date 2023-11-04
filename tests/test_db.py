from asyncio import run
from os import getenv as env
from dotenv import load_dotenv

from tortoise_api_model import init_db, model

load_dotenv()


def test_init_db():
    assert run(init_db(env('PG_DSN'), model)) == True, "DB corrupt"
