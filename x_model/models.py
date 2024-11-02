from datetime import datetime
from pydantic import create_model
from tortoise import Model as TortoiseModel
from tortoise.contrib.pydantic import pydantic_model_creator, PydanticModel
from tortoise import fields
from tortoise.exceptions import FieldError
from tortoise.models import MetaInfo
from tortoise.queryset import QuerySet
from x_model import HTTPException, FailReason

from x_model.field import DatetimeSecField
from x_model.pydantic import PydList


class BaseModel(TortoiseModel):
    # todo: resolve ownable + add only own list method
    # todo: refact: clean old garbage
    id: int = fields.IntField(True)

    _name: tuple[str] = ("name",)
    _sorts: tuple[str] = ("-id",)

    def repr(self, sep: str = " ") -> str:
        return sep.join(getattr(self, name_fragment) for name_fragment in self._name)

    @classmethod
    async def get_or_create_by_name(cls, name: str, attr_name: str = None, def_dict: dict = None) -> TortoiseModel:
        attr_name = attr_name or list(cls._name)[0]
        if not (obj := await cls.get_or_none(**{attr_name: name})):
            next_id = (await cls.all().order_by("-id").first()).id + 1
            obj = await cls.create(id=next_id, **{attr_name: name}, **(def_dict or {}))
        return obj

    @classmethod
    def _page_query(cls, sorts: tuple[str], limit: int = 1000, offset: int = 0, q: str = None, **filters) -> QuerySet:
        query = cls.filter(**filters).order_by(*sorts).limit(limit).offset(offset)
        if q:
            query = query.filter(**{f"{cls._name[0]}__icontains": q})
        return query

    @classmethod
    async def upsert(cls, data: dict, oid=None):
        meta: MetaInfo = cls._meta

        # pop fields for relations from general data dict # todo: add backwards fields for save
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
        obj = (await cls.update_or_create(data, id=oid))[0] if oid else await cls.create(**data)

        # save relations
        for k, ids in m2ms.items():
            if ids:
                m2m_rel: fields.ManyToManyRelation = getattr(obj, k)
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

    class Meta:
        abstract = True


class Model(BaseModel):
    _pyd: type[PydanticModel] = None
    _pydIn: type[PydanticModel] = None
    _pydListItem: type[PydanticModel] = None

    class PydanticMeta:
        # include: tuple[str, ...] = ()
        # exclude: tuple[str, ...] = ()
        # computed: tuple[str, ...] = ()
        exclude_raw_fields = False  # default: True
        max_recursion: int = 1  # default: 3

    class PydanticMetaIn:
        max_recursion: int = 0  # default: 3
        backward_relations: bool = False  # no need to disable when max_recursion=0  # default: True
        exclude_raw_fields: bool = False  # default: True

    class PydanticMetaListItem:
        max_recursion: int = 0  # default: 3
        backward_relations: bool = False  # default: True
        exclude_raw_fields = False  # default: True
        sort_alphabetically: bool = True  # default: False

    @classmethod
    def pyd(cls) -> type[PydanticModel]:
        cls._pyd = cls._pyd or pydantic_model_creator(cls, name=cls.__name__)
        return cls._pyd

    @classmethod
    def pyd_in(cls) -> type[PydanticModel]:
        if not cls._pydIn:
            opts = tuple(k for k, v in cls._meta.fields_map.items() if not v.required)
            cls._pydIn = pydantic_model_creator(
                cls,
                name=cls.__name__ + "In",
                meta_override=cls.PydanticMetaIn,
                optional=opts,
                exclude_readonly=True,
                exclude=("created_at", "updated_at"),
            )
            if m2ms := cls._meta.m2m_fields:  # hack for direct inserting m2m values
                cls._pydIn = create_model(
                    cls._pydIn.__name__, __base__=cls._pydIn, **{m2m: (list[int] | None, None) for m2m in m2ms}
                )
        return cls._pydIn

    @classmethod
    def pyd_list_item(cls) -> type[PydanticModel]:
        if not cls._pydListItem:
            cls._pydListItem = pydantic_model_creator(
                cls, name=cls.__name__ + "ListItem", meta_override=cls.PydanticMetaListItem
            )
        return cls._pydListItem

    @classmethod
    def pyds_list(cls) -> type[PydList]:
        return create_model(
            cls.__name__ + "List",
            data=(list[cls.pyd_list_item()], []),
            total=(int, 0),
            filtered=(int | None, None),
            __base__=PydList[cls.pyd_list_item()],
        )

    # # # CRUD Methods # # #
    @classmethod
    async def one_pyd(cls, uid: int, **filters) -> PydanticModel:
        q = cls.get(id=uid, **filters)
        return await cls.pyd().from_queryset_single(q)

    @classmethod
    async def page_pyd(cls, sorts: tuple[str], limit: int = 1000, offset: int = 0, q: str = None, **filters) -> PydList:
        filters = {k: v for k, v in filters.items() if v is not None}
        pyd_item = cls.pyd_list_item()
        query = cls._page_query(sorts, limit, offset, q, **filters)
        try:
            data = await pyd_item.from_queryset(query)
        except FieldError as e:
            raise HTTPException(FailReason.body, e)
        if limit - (li := len(data)):
            filtered = total = li + offset
        else:
            total = await cls.all().count()
            filtered_query = cls.filter(**filters)
            if q:
                filtered_query = filtered_query.filter(**{f"{cls._name}__icontains": q})
            filtered = await filtered_query.count()
        pyds = cls.pyds_list()
        return pyds(data=data, total=total, filtered=filtered)


class TsTrait:
    created_at: datetime | None = DatetimeSecField(auto_now_add=True)
    updated_at: datetime | None = DatetimeSecField(auto_now=True)
