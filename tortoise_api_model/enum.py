from enum import IntEnum


class FieldType(IntEnum):
    input = 1
    checkbox = 2
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
