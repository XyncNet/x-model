from asyncpg import Point, Polygon
from tortoise import Model as BaseModel
from tortoise.fields import Field


class Model(BaseModel):
    _name: str = 'name'
    def repr(self):
        if self._name in self._meta.db_fields:
            return getattr(self, self._name)
        return self.__repr__()


# Custom Fields
class PointField(Field[Point]):
    SQL_TYPE = "POINT"
    field_type = tuple[float, float]

class PolygonField(Field[Polygon]):
    SQL_TYPE = "POLYGON"
    field_type = tuple[tuple[float, float]]

