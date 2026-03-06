from enum import Enum, IntEnum


class EnvironmentName(str, Enum):
    LOCAL = "local"
    PRODUCT = "prod"

class SchemaType(Enum):
    TENANT = "tenant"
    COMMON = "common"


class ConditionEnum(str, Enum):
    like = "$like"
    not_like = "$not_like"
    ilike = "$ilike"
    in_c = "$in"
    not_in = "$not_in"
    eq = "$eq"
    neq = "$neq"
    gt = "$gt"
    lt = "$lt"
    gte = "$gte"
    lte = "$lte"
    between = "$between"
    not_between = "$not_between"
    contains = "$contains"
    not_contains = "$not_contains"
    contains_all = "$contains_all"
    contains_any = "$contains_any"

class DateFormat(str, Enum):
    YYYY_MM_DD = "%Y-%m-%d"
    DD_MM_YYYY = "%d-%m-%Y"
    MM_DD_YYYY = "%m-%d-%Y"

    YYYY_SLASH_MM_SLASH_DD = "%Y/%m/%d"
    DD_SLASH_MM_SLASH_YYYY = "%d/%m/%Y"

    YYYY_MM_DD_H = "%Y-%m-%d %H"
    YYYY_SLASH_MM_SLASH_DD_H = "%Y/%m/%d %H"
    DD_MM_YYYY_H = "%d-%m-%Y %H"

    YYYY_MM_DD_HM = "%Y-%m-%d %H:%M"
    YYYY_SLASH_MM_SLASH_DD_HM = "%Y/%m/%d %H:%M"
    DD_MM_YYYY_HM = "%d-%m-%Y %H:%M"

    YYYY_MM_DD_HMS = "%Y-%m-%d %H:%M:%S"
    YYYY_SLASH_MM_SLASH_DD_HMS = "%Y/%m/%d %H:%M:%S"
    DD_MM_YYYY_HMS = "%d-%m-%Y %H:%M:%S"

class StatusActive(IntEnum):
    UN_ACTIVE = 0
    ACTIVE = 1


class ListMustChooseLevel(IntEnum):
    REQUIRED = 1
    NOT_REQUIRED = 0

class ApiMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
