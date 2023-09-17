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
    Inactive = 0
    Wait = 1  # waiting for approve
    Test = 2  # trial
    Active = 3

class UserRole(IntEnum):
    Client = 0
    Manager = 1
    Agent = 2
    Admin = 3