from datetime import datetime
from passlib.context import CryptContext
from pydantic import create_model
from tortoise import Model as BaseModel
from tortoise.contrib.postgres.fields import ArrayField
from tortoise.contrib.pydantic import pydantic_model_creator, PydanticModel
from tortoise.contrib.pydantic.creator import PydanticMeta
from tortoise.fields import (
    Field,
    CharField,
    IntField,
    SmallIntField,
    BigIntField,
    DecimalField,
    FloatField,
    TextField,
    BooleanField,
    DatetimeField,
    DateField,
    TimeField,
    JSONField,
    ForeignKeyRelation,
    OneToOneRelation,
    ManyToManyRelation,
    ForeignKeyNullableRelation,
    OneToOneNullableRelation,
    IntEnumField,
)
from tortoise.fields.data import IntEnumFieldInstance, CharEnumFieldInstance
from tortoise.fields.relational import (
    BackwardFKRelation,
    ForeignKeyFieldInstance,
    ManyToManyFieldInstance,
    OneToOneFieldInstance,
    BackwardOneToOneRelation,
    RelationalField,
)
from tortoise.models import MetaInfo
from tortoise.queryset import QuerySet

from tortoise_api_model import FieldType, PointField, PolygonField, RangeField
from tortoise_api_model.enum import UserStatus, UserRole
from tortoise_api_model.field import DatetimeSecField, SetField
from tortoise_api_model.pydantic import PydList


class Model(BaseModel):
    id: int = IntField(pk=True)
    _name: set[str] = {"name"}
    _icon: str = ""  # https://unpkg.com/@tabler/icons@2.30.0/icons/icon_name.svg
    _sorts: list[str] = ["-id"]
    _ownable_fields: dict[str, str | None] = {"one": None, "list": None, "in": None}
    _pydIn: type[PydanticModel] = None
    _pyd: type[PydanticModel] = None
    _pydListItem: type[PydanticModel] = None
    _permissions: tuple[bool, bool, bool] = True, True, True

    @classmethod
    def cols(cls) -> list[dict]:
        meta = cls._meta
        return [
            {"data": c, "orderable": c not in meta.fetch_fields or c in meta.fk_fields}
            for c in meta.fields_map
            if not c.endswith("_id")
        ]

    @classmethod
    def pyd(
        cls,
        max_recursion: int = 1,
        backward_relations: bool = True,
        exclude: tuple[str, ...] = (),
        include: tuple[str, ...] = (),
        exclude_raw_fields: bool = True,
        force: bool = False,
    ) -> type[PydanticModel]:
        if not cls._pyd or force:
            mo = PydanticMeta
            mo.max_recursion = max_recursion
            mo.exclude_raw_fields = exclude_raw_fields  # default: True
            mo.backward_relations = backward_relations  # default: True
            cls._pyd = pydantic_model_creator(
                cls, name=cls.__name__, meta_override=mo, exclude=exclude, include=include
            )
        return cls._pyd

    @classmethod
    def pydIn(cls, exclude: tuple[str] = ()) -> type[PydanticModel]:
        if not cls._pydIn:
            mo = PydanticMeta
            mo.exclude_raw_fields = False
            mo.max_recursion = 0
            # mo.backward_relations = False # no need to disable backward relations, because recursion=0
            opts = tuple(k for k, v in cls._meta.fields_map.items() if not v.required)
            cls._pydIn = pydantic_model_creator(
                cls,
                name=cls.__name__ + "In",
                meta_override=mo,
                optional=opts,
                exclude_readonly=True,
                exclude=("created_at", "updated_at", *exclude),
            )
            if m2ms := cls._meta.m2m_fields:
                cls._pydIn = create_model(
                    cls._pydIn.__name__, __base__=cls._pydIn, **{m2m: (list[int] | None, None) for m2m in m2ms}
                )
        return cls._pydIn

    @classmethod
    def pydListItem(
        cls,
        max_recursion: int = 1,
        backward_relations: bool = False,
        exclude: tuple[str, ...] = (),
        include: tuple[str, ...] = (),
        force: bool = False,
    ) -> type[PydanticModel]:
        if not cls._pydListItem or force:
            mo = PydanticMeta
            mo.max_recursion = max_recursion
            mo.exclude_raw_fields = False  # default: True
            mo.backward_relations = backward_relations  # default: True
            cls._pydListItem = pydantic_model_creator(
                cls, name=cls.__name__ + "ListItem", meta_override=mo, exclude=exclude, include=include
            )
        return cls._pydListItem

    @classmethod
    def pydsList(cls) -> type[PydList]:
        return create_model(
            cls.__name__ + "List",
            data=(list[cls.pydListItem()], []),
            total=(int, 0),
            filtered=(int | None, None),
            __base__=PydList[cls.pydListItem()],
        )

    @classmethod
    async def one(cls, uid: int, owner: int = None, **kwargs) -> PydanticModel:
        if owner and (of := cls._ownable_fields.get("one")):
            kwargs.update({of: owner})
        q = cls.get(id=uid, **kwargs)
        return await cls.pyd().from_queryset_single(q)

    @classmethod
    def pageQuery(
        cls, sorts: list[str], limit: int = 1000, offset: int = 0, q: str = None, owner: int = None, **kwargs
    ) -> QuerySet:
        rels, keys = [], ["id"]
        for nam in cls._name:
            parts = nam.split("__")
            if len(parts) > 1:
                rels.append("__".join(parts[:-1]))
            keys.append(nam)
        query = (
            cls.filter(**kwargs)
            .order_by(*sorts)
            .limit(limit)
            .offset(offset)
            .prefetch_related(*(cls._meta.fetch_fields & set(kwargs)), *rels)
        )
        if q:
            query = query.filter(**{f"{cls._name}__icontains": q})
        if owner and (of := cls._ownable_fields.get("list")):
            query = query.filter(**{of: owner})
        return query

    @classmethod
    async def pagePyd(
        cls, sorts: list[str], limit: int = 1000, offset: int = 0, q: str = None, owner: int = None, **kwargs
    ) -> PydList:
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        pyd_args = {
            arg: kwargs.pop(arg)
            for arg in ("max_recursion", "backward_relations", "exclude", "include")
            if arg in kwargs
        }
        pyd = cls.pydListItem(**pyd_args, force=bool(pyd_args))
        query = cls.pageQuery(sorts, limit, offset, q, owner, **kwargs)
        await query
        data = await pyd.from_queryset(query)
        if limit - (li := len(data)):
            filtered = total = li + offset
        else:
            total = await cls.all().count()
            filtered_query = cls.filter(**kwargs)
            if q:
                filtered_query = filtered_query.filter(**{f"{cls._name}__icontains": q})
            filtered = await filtered_query.count()
        pyds = cls.pydsList()
        return pyds(data=data, total=total, filtered=filtered)

    def repr(self) -> str:
        if self._name in self._meta.db_fields:
            return " ".join(getattr(self, name_fragment) for name_fragment in self._name)
        return self.__repr__()

    @classmethod
    async def getOrCreateByName(cls, name: str, attr_name: str = None, def_dict: dict = None) -> BaseModel:
        attr_name = attr_name or cls._name
        if not (obj := await cls.get_or_none(**{attr_name: name})):
            next_id = (await cls.all().order_by("-id").first()).id + 1
            obj = await cls.create(id=next_id, **{attr_name: name}, **(def_dict or {}))
        return obj

    @classmethod
    async def upsert(cls, data: dict, oid=None):
        meta: MetaInfo = cls._meta

        # pop fields for relations from general data dict
        m2ms = {k: data.pop(k) for k in meta.m2m_fields if k in data}
        # bfks = {k: data.pop(k) for k in meta.backward_fk_fields if k in data}
        # bo2os = {k: data.pop(k) for k in meta.backward_o2o_fields if k in data}

        # save general model
        # if pk := meta.pk_attr in data.keys():
        #     unq = {pk: data.pop(pk)}
        # else:
        #     unq = {key: data.pop(key) for key, ft in meta.fields_map.items() if ft.unique and key in data.keys()}
        # # unq = meta.unique_together
        # obj, is_created = await cls.update_or_create(data, **unq)
        obj = (await cls.update_or_create(data, **{meta.pk_attr: oid}))[0] if oid else await cls.create(**data)

        # save relations
        for k, ids in m2ms.items():
            if ids:
                m2m_rel: ManyToManyRelation = getattr(obj, k)
                items = [await m2m_rel.remote_model[i] for i in ids]
                await m2m_rel.clear()  # for updating, not just adding
                await m2m_rel.add(*items)
        # for k, ids in bfks.items():
        #     bfk_rel: ReverseRelation = getattr(obj, k)
        #     items = [await bfk_rel.remote_model[i] for i in ids]
        #     [await item.update_from_dict({bfk_rel.relation_field: obj.pk}).save() for item in items]
        # for k, oid in bo2os.items():
        #     bo2o_rel: QuerySet = getattr(obj, k)
        #     item = await bo2o_rel.model[oid]
        #     await item.update_from_dict({obj._meta.db_table: obj}).save()

        await obj.fetch_related(*cls._meta.fetch_fields)
        return obj

    @classmethod
    def field_input_map(cls) -> dict:
        def type2input(ft: type[Field]):
            dry = {
                "base_field": hasattr(ft, "base_field") and {**type2input(ft.base_field)},
                "step": hasattr(ft, "step") and ft.step,
                "labels": hasattr(ft, "labels") and ft.labels,
            }
            type2inputs: {Field: dict} = {
                CharField: {"input": FieldType.input.name},
                IntField: {"input": FieldType.input.name, "type": "number"},
                SmallIntField: {"input": FieldType.input.name, "type": "number"},
                BigIntField: {"input": FieldType.input.name, "type": "number"},
                DecimalField: {"input": FieldType.input.name, "type": "number", "step": "0.01"},
                FloatField: {"input": FieldType.input.name, "type": "number", "step": "0.001"},
                TextField: {"input": FieldType.textarea.name, "rows": "2"},
                BooleanField: {"input": FieldType.checkbox.name},
                DatetimeField: {"input": FieldType.input.name, "type": "datetime"},
                DatetimeSecField: {"input": FieldType.input.name, "type": "datetime"},
                DateField: {"input": FieldType.input.name, "type": "date"},
                TimeField: {"input": FieldType.input.name, "type": "time"},
                JSONField: {"input": FieldType.input.name},
                IntEnumFieldInstance: {"input": FieldType.select.name},
                CharEnumFieldInstance: {"input": FieldType.select.name},
                ForeignKeyFieldInstance: {"input": FieldType.select.name},
                OneToOneFieldInstance: {"input": FieldType.select.name},
                ManyToManyFieldInstance: {"input": FieldType.select.name, "multiple": True},
                ForeignKeyRelation: {"input": FieldType.select.name, "multiple": True},
                OneToOneRelation: {"input": FieldType.select.name},
                BackwardOneToOneRelation: {"input": FieldType.select.name},
                ManyToManyRelation: {"input": FieldType.select.name, "multiple": True},
                ForeignKeyNullableRelation: {"input": FieldType.select.name, "multiple": True},
                BackwardFKRelation: {"input": FieldType.select.name, "multiple": True},
                ArrayField: {"input": FieldType.select.name, "multiple": True},
                SetField: {"input": FieldType.select.name, "multiple": True},
                OneToOneNullableRelation: {"input": FieldType.select.name},
                PointField: {"input": FieldType.collection.name, **dry},
                PolygonField: {"input": FieldType.list.name, **dry},
                RangeField: {"input": FieldType.collection.name, **dry},
            }
            return type2inputs[ft]

        def field2input(_key: str, field: Field):
            attrs: dict = {"required": not field.null}
            if isinstance(field, CharEnumFieldInstance):
                attrs.update({"options": {en.name: en.value for en in field.enum_type}})
            elif isinstance(field, IntEnumFieldInstance) or isinstance(field, SetField):
                attrs.update({"options": {en.value: en.name.replace("_", " ") for en in field.enum_type}})
            elif isinstance(field, RelationalField):
                attrs.update({"source_field": field.source_field})  # 'table': attrs[key]['multiple'],
            elif field.generated or ("auto_now" in field.__dict__ and (field.auto_now or field.auto_now_add)):  # noqa
                attrs.update({"auto": True})
            return {**type2input(type(field)), **attrs}

        return {key: field2input(key, field) for key, field in cls._meta.fields_map.items() if not key.endswith("_id")}

    class Meta:
        abstract = True


class TsModel(Model):
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)
    updated_at: datetime | None = DatetimeSecField(auto_now=True)

    class Meta:
        abstract = True


class User(TsModel):
    id: int = BigIntField(True)
    status: UserStatus = IntEnumField(UserStatus, default=UserStatus.wait)
    username: str | None = CharField(95, unique=True, null=True)
    email: str | None = CharField(100, unique=True, null=True)
    password: str | None = CharField(60, null=True)
    phone: int | None = BigIntField(null=True)
    role: UserRole = IntEnumField(UserRole, default=UserRole.Client)

    _icon = "user"
    _name = {"username"}

    __cc = CryptContext(schemes=["bcrypt"])

    def pwd_vrf(self, pwd: str) -> bool:
        return self.__cc.verify(pwd, self.password)

    @classmethod
    async def create(cls, using_db=None, **kwargs) -> "User":
        user: "User" | Model = await super().create(using_db, **kwargs)
        if pwd := kwargs.get("password"):
            await user.set_pwd(pwd)
        return user

    async def set_pwd(self, pwd: str = password) -> None:
        self.password = self.__cc.hash(pwd)
        await self.save()

    class Meta:
        table_description = "Users"
