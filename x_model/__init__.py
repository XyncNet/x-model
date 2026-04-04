from tortoise import Tortoise
from tortoise.backends.asyncpg import AsyncpgDBClient


async def init_db(conf: dict, create_tables: bool = False) -> AsyncpgDBClient | str:
    db_ctx = await Tortoise.init(conf, _enable_global_fallback=True)
    cn: AsyncpgDBClient = db_ctx.db("default")
    if create_tables:
        await cn.execute_script("CREATE EXTENSION IF NOT EXISTS uint128;")
        await Tortoise.generate_schemas()
    return cn
