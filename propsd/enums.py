from enum import Enum
from quart import json


class SourceStatus(Enum):
    """
    Source statuses
    """
    # pylint: disable=invalid-name
    OK = 'OK'
    NO_UPDATE = 'NO_UPDATE'
    NO_EXIST = 'NO_EXIST'
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class SourceState(Enum):
    """
    Source lifecycle states
    """
    # pylint: disable=invalid-name
    CREATED = 'CREATED'
    INITIALIZING = 'INITIALIZING'
    WAITING = 'WAITING'
    RUNNING = 'RUNNING'
    SHUTDOWN = 'SHUTDOWN'


class SourceEvents(Enum):
    # pylint: disable=invalid-name
    CREATED = 'CREATED'
    INITIALIZED = 'INITIALIZED'
    NO_UPDATE = 'NO_UPDATE'
    ERROR = 'ERROR'
    UPDATE = 'UPDATE'
    SHUTDOWN = 'SHUTDOWN'


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        return super().default(obj)
