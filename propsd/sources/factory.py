import logging
from typing import TYPE_CHECKING, Dict, Type, Optional, List

if TYPE_CHECKING:
    from propsd.sources.source import Source

_sources: Dict[str, Type['Source']] = {}
_logger: logging.Logger = logging.getLogger(__name__)


class SourceFactory:
    def __init__(self, source_type: str) -> None:
        self.type = source_type

    def __call__(self, cls: Type['Source']) -> Type['Source']:
        if self.type:
            cls.type = self.type
            _sources[self.type] = cls
            _logger.debug('SourceFactory: Registered %s source', self.type)
        return cls

    @staticmethod
    def new(source_type: str) -> Optional[Type['Source']]:
        source = _sources.get(source_type)
        if source is None:
            _logger.warning('SourceFactory: Unable to find source of type %s', source_type)
        return source
