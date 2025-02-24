import logging
from enum import IntEnum
from types import ModuleType

from tortoise import Tortoise, connections
from tortoise.backends.asyncpg import AsyncpgDBClient


async def init_db(dsn: str, models: ModuleType, create_tables: bool = False) -> AsyncpgDBClient | str:
    await Tortoise.init(db_url=dsn, modules={"models": [models]})
    if create_tables:
        await Tortoise.generate_schemas()
    cn: AsyncpgDBClient = connections.get("default")
    return cn


class FailReason(IntEnum):
    body = 8
    query = 9
    path = 10
    host = 11
    protocol = 12
    method = 13


class HTTPException(Exception):
    def __init__(
        self,
        reason: IntEnum,
        parent: Exception | str = None,
        status_: int = 400,
        hdrs: dict = None,
    ) -> None:
        detail = f"{reason.name}{f': {parent}' if parent else ''}"
        logging.error(detail)
        super().__init__(status_, detail, hdrs)
