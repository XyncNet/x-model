from datetime import datetime

from pydantic import ConfigDict
from tortoise import Model as BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator, PydanticModel
from tortoise.fields import DatetimeField, IntField

from x_model import HTTPException, FailReason


class DatetimeSecField(DatetimeField):
    class _db_postgres:
        SQL_TYPE = "TIMESTAMPTZ(0)"


class TsTrait:
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)
    updated_at: datetime | None = DatetimeSecField(auto_now=True)


class Model(BaseModel):
    id: int = IntField(True)

    _name: tuple[str] = ("name",)
    _sorts: tuple[str] = ("-id",)

    def repr(self) -> str:
        return " ".join(getattr(self, name_fragment) for name_fragment in self._name)

    @classmethod
    def _pyd(cls, suffix: str, **kwargs) -> type[PydanticModel]:
        return pydantic_model_creator(cls, name=cls.__name__ + suffix, **kwargs)

    @classmethod
    def pyd(cls):
        return cls._pyd("Root")

    @classmethod
    def pyd_in(cls):
        return cls._pyd("In", exclude_readonly=True)

    # # # CRUD Methods # # #
    @classmethod
    async def get_one(cls, id_: int, **filters) -> PydanticModel:
        if obj := await cls.get_or_none(id=id_, **filters):
            return await cls.pyd().from_tortoise_orm(obj)
        raise HTTPException(reason=FailReason.path, status_=404, parent=f"{cls.__name__}#{id_} not found")

    @classmethod
    async def get_or_create_by_name(cls, name: str, attr_name: str = None, def_dict: dict = None) -> "Model":
        attr_name = attr_name or list(cls._name)[0]
        if not (obj := await cls.get_or_none(**{attr_name: name})):
            next_id = (await cls.all().order_by("-id").first()).id + 1
            obj = await cls.create(id=next_id, **{attr_name: name}, **(def_dict or {}))
        return obj

    class PydanticMeta:
        model_config = ConfigDict(use_enum_values=True)
        # include: tuple[str, ...] = ()
        # exclude: tuple[str, ...] = ("Meta",)
        # computed: tuple[str, ...] = ()
        # backward_relations: bool = True
        max_recursion: int = 1  # default: 3
        # allow_cycles: bool = False
        # exclude_raw_fields: bool = True
        # sort_alphabetically: bool = False
        # model_config: ConfigDict | None = None

    class Meta:
        abstract = True
