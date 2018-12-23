# from collections import OrderedDict
# import hashlib
# import logging
# from datetime import datetime
# from typing import Any
#
# from pytz import utc
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from apscheduler.triggers.interval import IntervalTrigger
# from apscheduler.jobstores.memory import MemoryJobStore
# from apscheduler.events import JobExecutionEvent
# from apscheduler.job import Job
# from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
# from propsd.util.immutabledict import ImmutableDict
# from propsd import constants
#
# logger = logging.getLogger('{}.sources'.format(constants.APP_NAME))
#
# _jobstores = {
#     'default': MemoryJobStore()
# }
#
# _executors = {
#     'default': {
#         'type': 'asyncio'
#     }
# }
#
# _job_defaults = {
#     'coalesce': True,
#     'max_instances': -1
# }
#
#
# def _scheduler_event_logger(event: JobExecutionEvent):
#     if event.exception:
#         logger.error('%s: Job failed with traceback:\n%s', event.job_id, event.traceback)
#     else:
#         logger.info('%s: Job succeeded', event.job_id)
#
#
# def _generate_job_id(name: str) -> str:
#     job_hash = hashlib.sha1(name.encode('utf-8'))
#     return job_hash.hexdigest()
#
#
# class _Sources:
#     _sources: OrderedDict = OrderedDict()
#     _scheduler: AsyncIOScheduler = AsyncIOScheduler()
#     _properties: ImmutableDict = ImmutableDict()
#
#     def __init__(self, initial_properties):
#         self._scheduler.configure(jobstores=_jobstores,
#                                   executors=_executors,
#                                   job_defaults=_jobstores,
#                                   timezone=utc)
#         self._scheduler.add_listener(_scheduler_event_logger, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
#         if initial_properties:
#             self._properties = ImmutableDict(initial_properties)
#
#     def start(self):
#         self._scheduler.start()
#
#     def shutdown(self, wait=True):
#         self._scheduler.shutdown(wait)
#
#     def get(self, name: str) -> 'Source':
#         return self._sources[name]
#
#     def get_job(self, name: str) -> Job:
#         return self._scheduler.get_job(_generate_job_id(name))
#
#     def register(self, source: 'Source') -> None:
#         self._sources[source.name] = source
#
#     def unregister(self, name: str) -> None:
#         del self._sources[name]
#
#     def schedule(self, cls: 'Source', delay: int = 30):
#         self.register(cls)
#         source_name = str(cls)
#         trigger = IntervalTrigger(seconds=delay)
#         job_id = _generate_job_id(source_name)
#         self._scheduler.add_job(cls.get, args=(),
#                                 trigger=trigger,
#                                 id=job_id,
#                                 name=source_name,
#                                 max_instances=cls.instances)
#         # Immediately execute the job
#         job = self._scheduler.get_job(job_id)
#         job.modify(next_run_time=datetime.now())
#
#     def unschedule(self, cls: 'Source') -> None:
#         self.unregister(cls.name)
#         self._scheduler.remove_job(_generate_job_id(cls))
#
#     @property
#     def properties(self) -> ImmutableDict:
#         return self._properties
#
#     @properties.setter
#     def properties(self, value: Any) -> None:
#         pass
#
#
# def Sources(properties):  # pylint: disable=invalid-name
#     if properties:
#         return _Sources(properties)
#     else:
#         return _Sources()
