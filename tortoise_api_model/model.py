from asyncpg import Point, Polygon, Range
from tortoise import Model as BaseModel
from tortoise.fields import Field
from tortoise.fields.base import VALUE


class Model(BaseModel):
    # id: int = IntField(pk=True)
    _name: str = 'name'
    def repr(self):
        if self._name in self._meta.db_fields:
            return getattr(self, self._name)
        return self.__repr__()


# Custom Fields
class SeqField(Field[VALUE]):
    def to_python_value(self, value):
        if value is not None and not isinstance(value, self.field_type):
            value = self.field_type(*value)
        self.validate(value)
        return value

class RangeField(SeqField[Range]):
    SQL_TYPE = "int4range"
    field_type = Range

class PointField(SeqField[Point]):
    SQL_TYPE = "POINT"
    field_type = Point

class PolygonField(SeqField[Polygon]):
    SQL_TYPE = "POLYGON"
    field_type = Polygon
    base_field = PointField
