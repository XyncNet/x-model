from dataclasses import dataclass, asdict
from typing import ClassVar


@dataclass
class BaseUpd:
    _unq: ClassVar[set[str]]

    def df_unq(self, **kwargs) -> dict:
        d = {k: v for k, v in (asdict(self) | kwargs).items() if v is not None or k in self._unq}
        return {**{k: d.pop(k, None) for k in self._unq}, "defaults": d}
