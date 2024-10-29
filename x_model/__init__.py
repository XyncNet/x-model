import logging
from enum import IntEnum
from types import ModuleType

from starlette import status
from tortoise import Tortoise, connections, ConfigurationError
from tortoise.backends.asyncpg import AsyncpgDBClient
from tortoise.exceptions import DBConnectionError
from fastapi import HTTPException as BaseHTTPException


async def init_db(dsn: str, models: ModuleType, create_tables: bool = False) -> AsyncpgDBClient | str:
    try:
        await Tortoise.init(db_url=dsn, modules={"models": [models]})
        if create_tables:
            await Tortoise.generate_schemas()
        cn: AsyncpgDBClient = connections.get("default")
    except (ConfigurationError, DBConnectionError) as ce:
        return ce.args[0]
    return cn


class FailReason(IntEnum):
    body = 8
    query = 9
    path = 10
    host = 11
    protocol = 12
    method = 13


class HTTPException(BaseHTTPException):
    def __init__(
        self,
        reason: IntEnum,
        parent: Exception | str = None,
        status_: status = status.HTTP_400_BAD_REQUEST,
        hdrs: dict = None,
    ) -> None:
        detail = f"{reason.name}{f': {parent}' if parent else ''}"
        logging.error(detail)
        super().__init__(status_, detail, hdrs)
