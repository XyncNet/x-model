from enum import IntEnum


class FieldType(IntEnum):
    input = 1
    checkbox = 2
    select = 3
    textarea = 4
    collection = 5
    list = 6


class UserStatus(IntEnum):
    BANNED = 0
    WAIT = 1  # waiting for approve
    TEST = 2  # trial
    ACTIVE = 3
    PREMIUM = 4


class Scope(IntEnum):
    READ = 4
    WRITE = 2
    ALL = 1  # not only my


class UserRole(IntEnum):
    CLIENT = Scope.READ  # 4
    AUTHOR = Scope.WRITE  # 2
    MANAGER = Scope.READ + Scope.WRITE  # 6
    ADMIN = Scope.READ + Scope.WRITE + Scope.ALL  # 7
