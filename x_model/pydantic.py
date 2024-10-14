from typing import TypeVar, Generic
from pydantic import BaseModel, ConfigDict


RootModelType = TypeVar("RootModelType")


class PydList(BaseModel, Generic[RootModelType]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    data: list[RootModelType]
    total: int


class Names(BaseModel):
    # models for name endpoint for select2 inputs
    class Name(BaseModel):
        id: int
        text: str
        logo: str | None = None
        selected: bool | None = None

    class Pagination(BaseModel):
        more: bool

    results: list[Name]
    pagination: Pagination
