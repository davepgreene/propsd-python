from datetime import datetime
from typing import Optional, TYPE_CHECKING, Union

from propsd.enums import SourceEvents, SourceState
from propsd.sourcemanager import SourceManager
from propsd.util import dispatch

if TYPE_CHECKING:
    from apscheduler.job import Job


class Schedulable:
    updated: Optional[datetime] = None
    _state: Optional[SourceState] = None

    events: dict = {
        SourceEvents.CREATED: dispatch.Signal(providing_args=['source']),
        SourceEvents.INITIALIZED: dispatch.Signal(providing_args=['source']),
        SourceEvents.NO_UPDATE: dispatch.Signal(providing_args=['source']),
        SourceEvents.ERROR: dispatch.Signal(providing_args=['source', 'error']),
        SourceEvents.UPDATE: dispatch.Signal(providing_args=['source', 'data']),
        SourceEvents.SHUTDOWN: dispatch.Signal(providing_args=['source'])
    }

    def __init__(self):
        self._state = SourceState.CREATED
        self._send_event(SourceEvents.CREATED, source=self)

    def __repr__(self):
        return '{}.{}'.format(self.__class__.__name__, self._state)

    def _pre_get(self):
        if self._state == SourceState.CREATED:
            # First pass
            self._state = SourceState.INITIALIZING
        elif self._state == SourceState.WAITING:
            # Set running state
            self._state = SourceState.RUNNING

    def _post_get(self):
        self.updated = datetime.now()

        if self._state == SourceState.INITIALIZING:
            self._state = SourceState.WAITING
            self._send_event(SourceEvents.INITIALIZED, source=self)
        elif self._state == SourceState.RUNNING:
            # Reset to waiting state on success
            self._state = SourceState.WAITING

    @property
    def job(self) -> 'Job':
        return SourceManager.get_job(str(self))

    @property
    def available(self):
        return self._state in [SourceState.WAITING, SourceState.RUNNING]

    def shutdown(self):
        self._state = SourceState.SHUTDOWN
        self._send_event(SourceEvents.SHUTDOWN, source=self)

    def _send_event(self, event: SourceEvents, **kwargs: Optional[Union['Schedulable', dict]]) -> None:
        self.events[event].send_robust(sender=self.__class__, **kwargs)


def get_event(event: SourceEvents) -> dispatch.Signal:
    return Schedulable.events[event]
