from pydantic import BaseModel


class New(BaseModel):
    _unq: list[str] = []

    def df_unq(self) -> dict:
        d = self.model_dump(exclude_none=True)
        return {**{k: d.pop(k) for k in set(self._unq) & d.keys()}, "defaults": d}


class Upd(New):
    _unq: list[str] = ["id"]

    id: int
