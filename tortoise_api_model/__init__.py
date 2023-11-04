from types import ModuleType
from tortoise import Tortoise, connections, ConfigurationError
from tortoise.backends.asyncpg import AsyncpgDBClient
from tortoise.exceptions import DBConnectionError

from .enums import FieldType
from .fields import PointField, RangeField, PolygonField, CollectionField, ListField, DatetimeSecField
from .model import Model, TsModel, User


async def init_db(dsn: str, models: ModuleType) -> AsyncpgDBClient|str:
    try:
        await Tortoise.init(db_url=dsn, modules={'models': [models]})
        await Tortoise.generate_schemas()
        cn: AsyncpgDBClient = connections.get('default')
    except (ConfigurationError, DBConnectionError) as ce:
        return ce.args[0]
    return cn
