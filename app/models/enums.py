from enum import Enum


class GenderEnum(str, Enum):
    MALE = 'MALE'
    FEMALE = 'FEMALE'
    OTHER = 'OTHER'


class StatusEnum(str, Enum):
    ACTIVE = 'ACTIVE'
    COMPLETE = 'COMPLETE'
    INACTIVE = 'INACTIVE'
    INCOMPLETE = 'INCOMPLETE'


class PokedexStatusEnum(str, Enum):
    EMPTY = 'EMPTY'
    INITIALIZING = 'INITIALIZING'
    READY = 'READY'
    FAILED = 'FAILED'
