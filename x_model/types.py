from typing import ClassVar
from pydantic import BaseModel


class New(BaseModel):
    _unq: ClassVar[tuple[str]] = ()

    def df_unq(self) -> dict:
        d = {k: v for k, v in self.model_dump(exclude_none=True).items()}
        return {**{k: d.pop(k, None) for k in set(self._unq)}, "defaults": d}


class Upd(New):
    _unq = ("id",)

    id: int
