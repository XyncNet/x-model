from tortoise import Tortoise, connections
from tortoise.backends.asyncpg import AsyncpgDBClient


async def init_db(conf: dict, create_tables: bool = False) -> AsyncpgDBClient | str:
    await Tortoise.init(conf)
    cn: AsyncpgDBClient = connections.get("default")
    if create_tables:
        await cn.execute_script("CREATE EXTENSION IF NOT EXISTS uint128;")
        await Tortoise.generate_schemas()
    return cn
