from pydantic import BaseModel


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
