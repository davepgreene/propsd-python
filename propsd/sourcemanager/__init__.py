import hashlib
import json
import logging
import re
from collections import OrderedDict
from datetime import datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Optional, List, Tuple

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.events import JobExecutionEvent
from apscheduler.job import Job
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from jinja2 import Environment
from jinja2.exceptions import UndefinedError
from pytz import utc

from propsd.util import convert_to_object_access
from propsd.util.template import PreserveUndefined
from propsd.util.immutabledict import ImmutableDict
from propsd.util.remerge import remerge
from propsd.util.singleton import Singleton
from propsd.enums import SourceStatus

if TYPE_CHECKING:
    from propsd.sources.source import Source

logger = logging.getLogger(__name__)

_default_delay = 30

_jobstores = {
    'default': MemoryJobStore()
}

_executors = {
    'default': {
        'type': 'asyncio'
    }
}

_job_defaults = {
    'coalesce': True,
    'max_instances': -1,
    'misfire_grace_time': int(_default_delay / 3)  # We need enough of a grace period so we don't get repeated misfires
}


def _scheduler_event_logger(event: JobExecutionEvent):
    if event.exception:
        logger.error('%s: Job failed with traceback:\n%s', event.job_id, event.traceback)
    else:
        logger.info('%s: Job succeeded', event.job_id)


def _generate_job_id(name: str) -> str:
    job_hash = hashlib.sha1(name.strip().lower().encode('utf-8'))
    return job_hash.hexdigest()


def _put_in_dict(destination: dict, keys: str, delimiter: Optional[str] = '.', item: Optional[dict] = None):
    if delimiter in keys:
        key, rest = keys.split(delimiter, 1)
        if key not in destination:
            destination[key] = {}
        _put_in_dict(destination[key], rest, delimiter, item)
    else:
        if keys:
            destination[keys] = {} if item is None else item
        else:
            destination.update({} if item is None else item)


class SourceManager(metaclass=Singleton):
    class _Internal:
        sources: OrderedDict = OrderedDict()
        indices: OrderedDict = OrderedDict()
        scheduler: AsyncIOScheduler = AsyncIOScheduler()
        properties: ImmutableDict = ImmutableDict()
        update_hold_down = 1000

    _env = Environment(undefined=PreserveUndefined)

    def __init__(self, initial_properties: Optional[dict] = None):
        self._Internal.scheduler.configure(jobstores=_jobstores,
                                           executors=_executors,
                                           job_defaults=_job_defaults,
                                           timezone=utc)
        self._Internal.scheduler.add_listener(_scheduler_event_logger, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        if initial_properties:
            self._Internal.properties = ImmutableDict(initial_properties)

    ###
    # Meta scheduling methods
    ###
    @classmethod
    def start(cls):
        cls._Internal.scheduler.start()

    @classmethod
    def shutdown(cls, wait=True):
        cls._Internal.scheduler.shutdown(wait)

    @classmethod
    def get_job(cls, name: str) -> Job:
        return cls._Internal.scheduler.get_job(_generate_job_id(name))

    ###
    # Source management
    ###
    @classmethod
    def get(cls, name: str) -> 'Source':
        return cls._Internal.sources[name]

    @classmethod
    def register(cls, source: 'Source', namespace: str, index: bool = False) -> None:
        source_data = {
            'source': source,
            'namespace': namespace
        }
        if index:
            cls._Internal.indices[source.name] = source_data
        else:
            cls._Internal.sources[source.name] = source_data

    @classmethod
    def unregister(cls, name: str) -> None:
        del cls._Internal.sources[name]

    ###
    # Source scheduling
    ###
    @classmethod
    def schedule(cls, src: 'Source',
                 namespace: str = '',
                 index: bool = False,
                 delay: Optional[int] = _default_delay) -> None:
        # Make sure that we have a default delay if None is passed
        delay = _default_delay if not delay else delay
        logger.debug('SourceManager: Scheduling %s source', src.name)
        cls.register(src, namespace, index)
        source_name = str(src)
        trigger = IntervalTrigger(seconds=delay)
        job_id = _generate_job_id(source_name)
        existing_job = cls._Internal.scheduler.get_job(job_id)
        if existing_job:
            existing_job.remove()

        job = cls._Internal.scheduler.add_job(src.get, args=(),
                                              trigger=trigger,
                                              id=job_id,
                                              name=source_name,
                                              max_instances=src.instances)
        # Immediately execute the job
        job.modify(next_run_time=datetime.now())

    @classmethod
    def unschedule(cls, src: 'Source') -> None:
        cls.unregister(src.name)
        cls._Internal.scheduler.remove_job(_generate_job_id(str(src)))

    ###
    # Properties
    ###
    @classmethod
    def properties(cls) -> dict:
        all_properties: OrderedDict = OrderedDict()
        for name, source_data in cls._Internal.sources.items():
            source_properties: dict = {}
            source = source_data.get('source')
            # We don't want to include data from sources that aren't `ok`
            if not source.available:
                continue
            props = source.properties.to_dict() if isinstance(source.properties, ImmutableDict) else source.properties
            _put_in_dict(source_properties, source_data.get('namespace'), ':', props)
            all_properties[name] = source_properties
        merged = remerge(all_properties.values())
        final = remerge([merged, cls._Internal.properties])
        # Interpolate keys that have been set based on other values
        template = cls._env.from_string(
            re.sub(r'{{ ?(.+?) ?}}', convert_to_object_access, json.dumps(final))
        )
        try:
            return json.loads(template.render(final))
        except (UndefinedError, json.JSONDecodeError) as ex:
            # logger.error(ex)
            return final

    @classmethod
    def sources(cls) -> OrderedDict:
        return cls._Internal.sources

    @classmethod
    def indices(cls) -> OrderedDict:
        return cls._Internal.indices

    @classmethod
    def source_diff(cls, new_sources: List[Tuple[str, str]]) -> dict:
        existing_sources: List[Tuple[str, str]] = []
        for existing_source in cls.sources().values():
            source = existing_source.get('source')
            if source.name not in ['ec2-metadata', 'ec2-tags']:
                existing_sources.append((source.name, source.identity))
        to_add = [i for i in new_sources if i not in existing_sources]
        to_remove = [cls.sources().get(i[0], {}).get('source') for i in existing_sources if i not in new_sources]
        return {
            'add': to_add,
            'remove': to_remove
        }

    @classmethod
    def identity(cls, name, source_type, options):
        hashid = hashlib.sha1()
        for attr in [name, source_type, repr(sorted(frozenset(options.items()))).encode('utf-8')]:
            hashid.update(attr)

        return hashid.hexdigest()

    @classmethod
    def health(cls):
        resp = {
            'code': HTTPStatus.OK,
            'status': SourceStatus.OK,
            'indices': [],
            'sources': []
        }

        for i in cls.indices().values():
            idx = i.get('source')
            if not idx.ok:
                idx_status = idx.status()
                resp['code'] = HTTPStatus.INTERNAL_SERVER_ERROR
                resp['status'] = idx_status.get('status')
            resp['indices'].append(idx.status())

        for source in cls.sources().values():
            source = source.get('source')
            source_status = source.status()
            if not source.ok:
                resp['code'] = HTTPStatus.INTERNAL_SERVER_ERROR
                resp['status'] = source_status.get('status')
            resp['sources'].append(source.status())
        return resp
