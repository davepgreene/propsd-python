from typing import Optional, Mapping
from enum import Enum
from apscheduler.job import Job

from propsd.util.dispatch import Signal
from propsd.util.immutabledict import ImmutableDict
from propsd.lib import Sources
from propsd.util import dispatch


class SourceStatus(Enum):
    # pylint: disable=invalid-name
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


class SourceEvents(Enum):
    # pylint: disable=invalid-name
    CREATED = 'CREATED'
    INITIALIZED = 'INITIALIZED'
    NO_UPDATE = 'NO_UPDATE'
    ERROR = 'ERROR'
    UPDATE = 'UPDATE'
    SHUTDOWN = 'SHUTDOWN'


class Source:
    _properties: ImmutableDict = ImmutableDict()
    _options: dict = {}
    _state: Optional[str] = None

    events: dict = {
        SourceEvents.CREATED: dispatch.Signal(providing_args=['source']),
        SourceEvents.INITIALIZED: dispatch.Signal(providing_args=['source']),
        SourceEvents.NO_UPDATE: dispatch.Signal(providing_args=['source']),
        SourceEvents.ERROR: dispatch.Signal(providing_args=['source', 'error']),
        SourceEvents.UPDATE: dispatch.Signal(providing_args=['source', 'data']),
        SourceEvents.SHUTDOWN: dispatch.Signal(providing_args=['source'])
    }

    def __init__(self, name: str, instances: Optional[int] = None, opts: Optional[object] = None) -> None:
        if not name:
            raise NotImplementedError('Source: Sources must have a `name` parameter.')

        self.name = name
        self.instances = instances
        if opts:
            self._options = opts
        self._state = SourceStatus.CREATED
        self._send_event(SourceEvents.CREATED, source=self)

    @property
    def job(self) -> Job:
        return Sources.get_job(str(self))

    def get(self):
        raise NotImplementedError('`get` must be implemented in `Source` subclasses.')

    @property
    def properties(self) -> ImmutableDict:
        return self._properties

    @properties.setter
    def properties(self, properties: Mapping):
        self._properties = self._properties.update(**properties)

    def status(self):
        return {
            'state': self._state
        }

    def _send_event(self, event: SourceEvents, **kwargs: Optional[dict]) -> None:
        self.events[event].send_robust(sender=self.__class__, **kwargs)

    def __repr__(self):
        return '{}.{}'.format(self.__class__.__name__, self.name)


def get_event(event: SourceEvents) -> Signal:
    return Source.events[event]
