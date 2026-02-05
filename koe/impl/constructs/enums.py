import enum


class RepeatMode(enum.Enum):
    ONE = "ONE"
    ALL = "ALL"
    NONE = "NONE"


class SessionMode(enum.Enum):
    TRANSIENT = "TRANSIENT"
    PERSISTENT = "PERSISTENT"