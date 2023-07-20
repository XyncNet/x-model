from tortoise import Model as BaseModel

class Model(BaseModel):
    _name: str = 'name'
    def repr(self):
        if self._name in self._meta.db_fields:
            return getattr(self, self._name)
        return self.__repr__()
