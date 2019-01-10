import logging
from typing import Optional, Mapping, Union, Type, TYPE_CHECKING

from propsd.enums import SourceStatus, SourceState
from propsd.sourcemanager import SourceManager
from propsd.sources.schedulable import Schedulable
from propsd.util.immutabledict import ImmutableDict

if TYPE_CHECKING:
    from propsd.sources.parser import Parser


class Source(Schedulable):
    _properties: ImmutableDict = ImmutableDict()
    options: dict = {}
    type: str = ''
    name: str = ''
    _status: Optional[SourceStatus] = None
    _signature: Optional[Union[str, bytes]] = None
    _logger: logging.Logger = logging.getLogger(__name__)
    _parser: Optional[Type['Parser']] = None

    def __init__(self, name: str, instances: Optional[int] = None, opts: Optional[dict] = None) -> None:
        super().__init__()
        if not name:
            raise NotImplementedError('Source: Sources must have a `name` parameter.')

        self.name = name
        self.instances = instances
        if opts:
            self.options = opts

    def __repr__(self):
        return '{}.{}'.format(self.__class__.__name__, self.name)

    @property
    def identity(self) -> str:
        return SourceManager.identity(self.name.encode('utf-8'), self.type.encode('utf-8'), self.options)

    @property
    def properties(self) -> ImmutableDict:
        return self._properties

    @properties.setter
    def properties(self, properties: Mapping, merge: bool = False):
        self._properties = self._properties.update(**properties) if merge else ImmutableDict(properties)

    @property
    def ok(self):
        return self._status not in [SourceStatus.ERROR, SourceStatus.WARNING, SourceState.SHUTDOWN]

    def status(self):
        return {
            'name': self.name,
            'type': self.type,
            'ok': self.ok,
            'state': self._state,
            'status': self._status,
            'updated': self.updated
        }

    async def get(self):
        if self._state == SourceState.SHUTDOWN:
            self._logger.info('Source: Source {} has been shutdown, but not unscheduled.'.format(self.name))
            return
        self._pre_get()
        self._get()
        self._post_get()

    def _get(self):
        raise NotImplementedError('`_get` must be implemented in `Source` subclasses.')
