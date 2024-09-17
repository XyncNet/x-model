from pypika.terms import AggregateFunction
from tortoise.expressions import Function


class ArrayAgg(AggregateFunction):
    def __init__(self, term, alias=None):
        super(ArrayAgg, self).__init__("array_agg", term, alias=alias)


class Array(Function):
    database_func = ArrayAgg
