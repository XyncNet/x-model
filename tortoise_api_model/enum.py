from enum import IntEnum


class FieldType(IntEnum):
    # str = 1
    # txt = 2
    # int = 3
    # float = 4
    # date = 8
    # time = 9
    # dt = 10
    input = 1
    checkbox = 2
    # one = 11
    # many = 12
    select = 3
    textarea = 4
    collection = 5
    list = 6


class UserStatus(IntEnum):
    banned = 0
    wait = 1  # waiting for approve
    test = 2  # trial
    active = 3


class UserRole(IntEnum):
    Client = 1
    Agent = 2
    Manager = 3
    Admin = 4


class Scope(IntEnum):
    Read = 1
    Write = 2
    All = 3  # not only my
