from copy import copy
from typing import TypeVar, Generic
from pydantic import BaseModel, ConfigDict
from tortoise.contrib.pydantic.creator import PydanticMeta

from tortoise_api_model.enum import UserStatus, UserRole

In = PydanticMeta
In.exclude_raw_fields = False
In.max_recursion = 0
# In.backward_relations = False # no need to disable backward relations, because recursion=0

Out = copy(PydanticMeta)
Out.max_recursion = 1
Out.backward_relations = True
Out.exclude_raw_fields = True # no need to override to the True, True is default

ListItem = copy(Out)
ListItem.backward_relations = False

RootModelType = TypeVar('RootModelType')
class PydList(BaseModel, Generic[RootModelType]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    data: list[RootModelType]
    total: int

class UserPwd(BaseModel):
    password: str

class UserReg(UserPwd):
    username: str
    email: str|None = None
    phone: int|None = None

class UserUpdate(BaseModel):
    username: str
    status: UserStatus
    email: str|None
    phone: int|None
    role: UserRole

class UserSchema(UserUpdate):
    id: int
