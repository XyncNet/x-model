from datetime import datetime
from passlib.context import CryptContext
from pydantic import create_model
from tortoise import Model as BaseModel
from tortoise.contrib.postgres.fields import ArrayField
from tortoise.contrib.pydantic import pydantic_model_creator, PydanticModel
from tortoise.contrib.pydantic.creator import PydanticMeta
from tortoise.fields import Field, CharField, IntField, SmallIntField, BigIntField, DecimalField, FloatField,\
    TextField, BooleanField, DatetimeField, DateField, TimeField, JSONField, ForeignKeyRelation, OneToOneRelation, \
    ManyToManyRelation, ForeignKeyNullableRelation, OneToOneNullableRelation, IntEnumField
from tortoise.fields.data import IntEnumFieldInstance, CharEnumFieldInstance
from tortoise.fields.relational import BackwardFKRelation, ForeignKeyFieldInstance, ManyToManyFieldInstance, \
    OneToOneFieldInstance, BackwardOneToOneRelation, RelationalField, ReverseRelation
from tortoise.models import MetaInfo
from tortoise.queryset import QuerySet

from tortoise_api_model import FieldType, PointField, PolygonField, RangeField
from tortoise_api_model.enum import UserStatus, UserRole
from tortoise_api_model.field import DatetimeSecField, SetField
from tortoise_api_model.pydantic import PydList


class Model(BaseModel):
    id: int = IntField(pk=True)
    _name: str = 'name'
    _icon: str = '' # https://unpkg.com/@tabler/icons@2.30.0/icons/icon_name.svg
    _sorts: list[str] = ['-id']
    _pydIn: type[PydanticModel] = None
    _pyd: type[PydanticModel] = None
    _pydListItem: type[PydanticModel] = None

    @classmethod
    def cols(cls) -> list[dict]:
        meta = cls._meta
        return [{'data': c, 'orderable': c not in meta.fetch_fields or c in meta.fk_fields} for c in meta.fields_map if not c.endswith('_id')]

    @classmethod
    def pyd(cls) -> type[PydanticModel]:
        if not cls._pyd:
            mo = PydanticMeta
            mo.max_recursion = 1
            mo.exclude_raw_fields = True
            mo.backward_relations = True
            # mo.exclude_raw_fields = True # no need to override to the True, True is default
            cls._pyd = pydantic_model_creator(cls, name=cls.__name__, meta_override=mo)
        return cls._pyd

    @classmethod
    def pydIn(cls) -> type[PydanticModel]:
        if not cls._pydIn:
            mo = PydanticMeta
            mo.exclude_raw_fields = False
            mo.max_recursion = 0
            # mo.backward_relations = False # no need to disable backward relations, because recursion=0
            cls._pydIn = pydantic_model_creator(cls, name=cls.__name__+'In', meta_override=mo, **{'exclude_readonly': True, 'exclude': ('created_at', 'updated_at')})
        return cls._pydIn

    @classmethod
    def pydListItem(cls) -> type[PydanticModel]:
        if not cls._pydListItem:
            mo = PydanticMeta
            mo.max_recursion = 1
            mo.exclude_raw_fields = True # default: True
            mo.backward_relations = False # default: True
            cls._pydListItem = pydantic_model_creator(cls, name=cls.__name__+'ListItem', meta_override=mo)
        return cls._pydListItem

    @classmethod
    def pydsList(cls) -> type[PydList]:
        return create_model(
            cls.__name__ + 'List',
            data=(list[cls.pydListItem()], []),
            total=(int, 0),
            __base__=PydList[cls.pydListItem()],
        )

    @classmethod
    async def one(cls, uid: int) -> PydanticModel:
        q = cls.get(id=uid)
        return await cls.pyd().from_queryset_single(q)

    @classmethod
    def pageQuery(cls, sorts: list[str], limit: int = 1000, offset: int = 0, q: str = None, **kwargs) -> QuerySet:
        query = cls.filter(**kwargs).order_by(*sorts).limit(limit).offset(offset).prefetch_related(*kwargs)
        if '__' in cls._name: # if name field needs to be fetched
            query = query.prefetch_related('__'.join(cls._name.split('__')[:-1]))
        if q:
            query = query.filter(**{f'{cls._name}__istartswith': q})
        return query

    @classmethod
    async def pagePyd(cls, sorts: list[str], limit: int = 1000, offset: int = 0, q: str = None, **kwargs) -> PydList:
        pyd = cls.pydListItem()
        kwargs = {k: v for k, v in kwargs.items() if v}
        query = cls.pageQuery(sorts, limit, offset, q, **kwargs)
        data = await pyd.from_queryset(query)
        total = l+offset if limit-(l:=len(data)) else await cls.all().count()
        pyds = cls.pydsList()
        return pyds(data=data, total=total)

    def repr(self):
        if self._name in self._meta.db_fields:
            return getattr(self, self._name)
        return self.__repr__()

    @classmethod
    async def getOrCreateByName(cls, name: str, attr_name: str = None, def_dict: dict = None) -> BaseModel:
        attr_name = attr_name or cls._name
        if not (obj := await cls.get_or_none(**{attr_name: name})):
            next_id = (await cls.all().order_by('-id').first()).id + 1
            obj = await cls.create(id=next_id, **{attr_name: name}, **(def_dict or {}))
        return obj


    @classmethod
    async def upsert(cls, data: dict, oid = None):
        meta: MetaInfo = cls._meta

        # pop fields for relations from general data dict
        m2ms = {k: data.pop(k) for k in meta.m2m_fields if k in data}
        bfks = {k: data.pop(k) for k in meta.backward_fk_fields if k in data}
        bo2os = {k: data.pop(k) for k in meta.backward_o2o_fields if k in data}

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
            m2m_rel: ManyToManyRelation = getattr(obj, k)
            items = [await m2m_rel.remote_model[i] for i in ids]
            await m2m_rel.add(*items)
        for k, ids in bfks.items():
            bfk_rel: ReverseRelation = getattr(obj, k)
            items = [await bfk_rel.remote_model[i] for i in ids]
            [await item.update_from_dict({bfk_rel.relation_field: obj.pk}).save() for item in items]
        for k, oid in bo2os.items():
            bo2o_rel: QuerySet = getattr(obj, k)
            item = await bo2o_rel.model[oid]
            await item.update_from_dict({obj._meta.db_table: obj}).save()

        await obj.fetch_related(*cls._meta.fetch_fields)
        return obj

    @classmethod
    def field_input_map(cls) -> dict:
        def type2input(ft: type[Field]):
            dry = {
                'base_field': hasattr(ft, 'base_field') and {**type2input(ft.base_field)},
                'step': hasattr(ft, 'step') and ft.step,
                'labels': hasattr(ft, 'labels') and ft.labels
            }
            type2inputs: {Field: dict} = {
                CharField: {'input': FieldType.input.name},
                IntField: {'input': FieldType.input.name, 'type': 'number'},
                SmallIntField: {'input': FieldType.input.name, 'type': 'number'},
                BigIntField: {'input': FieldType.input.name, 'type': 'number'},
                DecimalField: {'input': FieldType.input.name, 'type': 'number', 'step': '0.01'},
                FloatField: {'input': FieldType.input.name, 'type': 'number', 'step': '0.001'},
                TextField: {'input': FieldType.textarea.name, 'rows': '2'},
                BooleanField: {'input': FieldType.checkbox.name},
                DatetimeField: {'input': FieldType.input.name, 'type': 'datetime'},
                DatetimeSecField: {'input': FieldType.input.name, 'type': 'datetime'},
                DateField: {'input': FieldType.input.name, 'type': 'date'},
                TimeField: {'input': FieldType.input.name, 'type': 'time'},
                JSONField: {'input': FieldType.input.name},
                IntEnumFieldInstance: {'input': FieldType.select.name},
                CharEnumFieldInstance: {'input': FieldType.select.name},
                ForeignKeyFieldInstance: {'input': FieldType.select.name},
                OneToOneFieldInstance: {'input': FieldType.select.name},
                ManyToManyFieldInstance: {'input': FieldType.select.name, 'multiple': True},
                ForeignKeyRelation: {'input': FieldType.select.name, 'multiple': True},
                OneToOneRelation: {'input': FieldType.select.name},
                BackwardOneToOneRelation: {'input': FieldType.select.name},
                ManyToManyRelation: {'input': FieldType.select.name, 'multiple': True},
                ForeignKeyNullableRelation: {'input': FieldType.select.name, 'multiple': True},
                BackwardFKRelation: {'input': FieldType.select.name, 'multiple': True},
                ArrayField: {'input': FieldType.select.name, 'multiple': True},
                SetField: {'input': FieldType.select.name, 'multiple': True},
                OneToOneNullableRelation: {'input': FieldType.select.name},
                PointField: {'input': FieldType.collection.name, **dry},
                PolygonField: {'input': FieldType.list.name, **dry},
                RangeField: {'input': FieldType.collection.name, **dry},
            }
            return type2inputs[ft]

        def field2input(key: str, field: Field):
            attrs: dict = {'required': not field.null}
            if isinstance(field, CharEnumFieldInstance):
                attrs.update({'options': {en.name: en.value for en in field.enum_type}})
            elif isinstance(field, IntEnumFieldInstance) or isinstance(field, SetField):
                attrs.update({'options': {en.value: en.name.replace('_', ' ') for en in field.enum_type}})
            elif isinstance(field, RelationalField):
                attrs.update({'source_field': field.source_field})  # 'table': attrs[key]['multiple'],
            elif field.generated or ('auto_now' in field.__dict__ and (field.auto_now or field.auto_now_add)): # noqa
                attrs.update({'auto': True})
            return {**type2input(type(field)), **attrs}

        return {key: field2input(key, field) for key, field in cls._meta.fields_map.items() if not key.endswith('_id')}

    class Meta:
        abstract = True


class TsModel(Model):
    created_at: datetime|None = DatetimeSecField(auto_now_add=True)
    updated_at: datetime|None = DatetimeSecField(auto_now=True)

    class Meta:
        abstract = True


class User(TsModel):
    id: int = SmallIntField(True)
    status: UserStatus = IntEnumField(UserStatus, default=UserStatus.wait)
    username: str = CharField(95, unique=True)
    email: str|None = CharField(100, unique=True, null=True)
    password: str|None = CharField(60, null=True)
    phone: int|None = BigIntField(null=True)
    role: UserRole = IntEnumField(UserRole, default=UserRole.Client)

    _icon = 'user'
    _name = 'username'

    __cc = CryptContext(schemes=["bcrypt"])

    def pwd_vrf(self, pwd: str) -> bool:
        return self.__cc.verify(pwd, self.password)

    @classmethod
    async def create(cls, using_db = None, **kwargs) -> "User":
        user: "User"|Model = await super().create(using_db, **kwargs)
        await user.update_from_dict({'password': cls.__cc.hash(user.password)}).save(using_db, update_fields=['password'])
        return user

    class Meta:
        table_description = "Users"
