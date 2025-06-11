from tortoise import Tortoise, connections
from tortoise.backends.asyncpg import AsyncpgDBClient


async def init_db(conf: dict, create_tables: bool = True) -> AsyncpgDBClient | str:
    await Tortoise.init(conf)
    if create_tables:
        await Tortoise.generate_schemas()
    cn: AsyncpgDBClient = connections.get("default")
    return cn
