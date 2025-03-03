from datetime import datetime
from pydantic import ConfigDict, BaseModel
from tortoise import Model as TrtModel
from tortoise.contrib.pydantic import pydantic_model_creator, PydanticModel
from tortoise.fields import IntField

from x_model.field import DatetimeSecField


class TsTrait:
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)
    updated_at: datetime | None = DatetimeSecField(auto_now=True)


class PydIn(BaseModel):
    _unq: list[str] = ["id"]

    def df_unq(self) -> dict:
        d = self.model_dump(exclude_none=True)
        return {**{k: d.pop(k) for k in self._unq}, "defaults": d}


class Model(TrtModel):
    id: int = IntField(True)

    _pyd: type[PydanticModel] = None  # overridable
    _pydIn: type[PydIn | PydanticModel] = None  # overridable
    _name: tuple[str] = ("name",)
    _sorts: tuple[str] = ("-id",)

    def repr(self) -> str:
        return " ".join(getattr(self, name_fragment) for name_fragment in self._name)

    @classmethod
    def pyd(cls):
        if not cls._pyd:
            cls._pyd = pydantic_model_creator(cls, name=cls.__name__)
        return cls._pyd

    @classmethod
    def pyd_in(cls):
        if not cls._pydIn:
            cls._pydIn = pydantic_model_creator(
                cls, name=cls.__name__ + "In", exclude_readonly=True, meta_override=cls.PydanticMetaIn
            )
        return cls._pydIn

    # # # CRUD Methods # # #
    @classmethod
    async def get_one(cls, id_: int) -> PydanticModel:
        if obj := await cls.get_or_none(id=id_):
            return await cls.pyd().from_tortoise_orm(obj)
        raise LookupError(f"{cls.__name__}#{id_} not found")

    async def one(self) -> PydanticModel:
        return await self.pyd().from_tortoise_orm(self)

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

    class PydanticMetaIn:
        backward_relations: bool = False
        max_recursion: int = 0
        exclude_raw_fields: bool = False

    class Meta:
        abstract = True
