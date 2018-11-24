import sched
import time
from propsd.sources.exceptions import SourceSchedulingError
from propsd.sources.source import Source


def schedule(cls: Source, delay: int = 30) -> Source:
    if not isinstance(cls, Source):
        raise SourceSchedulingError("Scheduled class must be subclass of `Source`")

    cls.scheduler = 'foo'
    return cls


