from types import ModuleType

from tortoise import Tortoise, connections
from tortoise.backends.asyncpg import AsyncpgDBClient


async def init_db(dsn: str, models: ModuleType, create_tables: bool = True) -> AsyncpgDBClient | str:
    await Tortoise.init(db_url=dsn, modules={"models": [models]})
    if create_tables:
        await Tortoise.generate_schemas()
    cn: AsyncpgDBClient = connections.get("default")
    return cn
