from asyncpg import Point, Polygon
from tortoise import Model as BaseModel
from tortoise.fields import Field


class Model(BaseModel):
    # id: int = IntField(pk=True)
    _name: str = 'name'
    def repr(self):
        if self._name in self._meta.db_fields:
            return getattr(self, self._name)
        return self.__repr__()


# Custom Fields
class PointField(Field[Point]):
    SQL_TYPE = "POINT"
    field_type = Point

    def to_python_value(self, value):
        if value is not None and not isinstance(value, Point):
            value = Point(*value)  # pylint: disable=E1102
        self.validate(value)
        return value

class PolygonField(Field[Polygon]):
    SQL_TYPE = "POLYGON"
    field_type = Polygon
    base_field = PointField

    def to_python_value(self, value):
        if value is not None and not isinstance(value, Polygon):
            value = Polygon(*value)  # pylint: disable=E1102
        self.validate(value)
        return value
