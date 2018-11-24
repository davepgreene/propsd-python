from typing import Optional
from enum import Enum


class SourceStatus(Enum):
    # Non - data responses from provider resources
    NO_UPDATE = 'NO_UPDATE'
    NO_EXIST = 'NO_EXIST'
    # Lifecycle states
    CREATED = 'CREATED'
    INITIALIZING = 'INITIALIZING'
    WAITING = 'WAITING'
    RUNNING = 'RUNNING'
    SHUTDOWN = 'SHUTDOWN'
    # Error States
    WARNING = 'WARNING'
    ERROR = 'ERROR'


class Source:
    _scheduler = None

    def __init__(self, opts: Optional[object] = None):
        pass

    @property
    def scheduler(self):
        return self._scheduler

    @scheduler.setter
    def scheduler(self, scheduler):
        self._scheduler = scheduler

    def startup(self):
        pass

    def shutdown(self):
        pass

    def get(self):
        raise NotImplementedError("`get` must be implemented in `Source` subclasses.")
