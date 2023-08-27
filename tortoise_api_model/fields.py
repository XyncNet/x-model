from asyncpg import Point, Polygon, Range
from tortoise.fields import Field, IntField, FloatField, DatetimeField
from tortoise.fields.base import VALUE


class ListField(Field[VALUE]):
    base_field = Field[VALUE]
    labels: tuple

    # def __getattr__(self, attr):
    #     return None

    def to_python_value(self, value):
        if value is not None and not isinstance(value, self.field_type):
            value = self.field_type(*value)
        self.validate(value)
        return value

class CollectionField(ListField[VALUE]):
    labels: tuple
    step: str = None

    def __new__(cls, precision: int = 0, *args, **kwargs):
        if precision:
            cls.step = f"0.{'0'*(precision-1)}1"
        cls.base_field = FloatField if precision else IntField
        return super().__new__(cls)


class RangeField(CollectionField[Range]):
    field_type = Range
    labels = ("from", "to")

    def __new__(cls, precision: int = 0, *args, **kwargs):
        cls.SQL_TYPE = "numrange" if precision else "int4range"
        return super().__new__(cls)

    def to_python_value(self, value):
        if value is not None and not isinstance(value, self.field_type):
            value = self.field_type(*[float(v) for v in value])
        self.validate(value)
        return value

class PointField(CollectionField[Point]):
    SQL_TYPE = "POINT"
    field_type = Point
    base_field = FloatField
    labels = ("lat", "lon")

class PolygonField(ListField[Polygon]):
    SQL_TYPE = "POLYGON"
    field_type = Polygon
    base_field = PointField


class DatetimeSecField(DatetimeField):
    class _db_postgres:
        SQL_TYPE = "TIMESTAMPTZ(0)"

# class InetField(CollectionField[Point]):
#     SQL_TYPE = "INET"
#     field_type = Point
#     base_field = FloatField
#     labels = ("lat", "lon")
