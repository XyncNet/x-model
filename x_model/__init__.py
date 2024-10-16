from types import ModuleType
from tortoise import Tortoise, connections, ConfigurationError
from tortoise.backends.asyncpg import AsyncpgDBClient
from tortoise.exceptions import DBConnectionError


async def init_db(dsn: str, models: ModuleType, create_tables: bool = False) -> AsyncpgDBClient | str:
    try:
        await Tortoise.init(db_url=dsn, modules={"models": [models]})
        if create_tables:
            await Tortoise.generate_schemas()
        cn: AsyncpgDBClient = connections.get("default")
    except (ConfigurationError, DBConnectionError) as ce:
        return ce.args[0]
    return cn
