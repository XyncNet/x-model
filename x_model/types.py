from typing import ClassVar
from msgspec import Struct
from msgspec.structs import asdict


class New(Struct):
    _unq: ClassVar[tuple[str]] = ()

    def df_unq(self, frozen_props: tuple[str] = ()) -> dict:
        d = {k: v for k, v in asdict(self).items() if v is not None or k in frozen_props}
        return {**{k: d.pop(k) for k in set(self._unq) & d.keys()}, "defaults": d}


class Upd(New):
    _unq = ("id",)

    id: int
