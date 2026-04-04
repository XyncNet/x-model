from dataclasses import dataclass, asdict
from json import dumps
from typing import ClassVar, Self
from msgspec import Struct, to_builtins, convert


@dataclass
class BaseUpd:
    _unq: ClassVar[set[str]]

    def df_unq(self, **kwargs) -> dict:
        d = {k: v for k, v in (asdict(self) | kwargs).items() if v is not None or k in self._unq}
        return {**{k: d.pop(k, None) for k in self._unq}, "defaults": d}


class Xs(Struct):
    @classmethod
    def dec_hook(cls, *args, **kwargs):
        pass

    def dump(self, nones: bool = False) -> dict:
        return {k: v for k, v in to_builtins(self).items() if nones or v is not None}

    def json(self, nones: bool = False) -> str:
        return dumps(self.dump(nones))

    @classmethod
    def load(cls, obj, **kwargs) -> Self:
        dct = dict(obj)
        return convert({**dct, **kwargs}, cls, dec_hook=cls.dec_hook)  # , strict=False
