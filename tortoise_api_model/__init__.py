from types import ModuleType
from tortoise import Tortoise

from .enums import FieldType
from .fields import PointField, RangeField, PolygonField, CollectionField, ListField, DatetimeSecField
from .model import Model, TsModel, User


async def init_db(dsn: str, models: ModuleType):
    await Tortoise.init(db_url=dsn, modules={'models': [models]})
    await Tortoise.generate_schemas()
    return True
