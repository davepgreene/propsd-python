import logging
from typing import Optional

import consul
from requests.exceptions import ConnectionError

from propsd.config import settings
from propsd.sources.factory import SourceFactory
from propsd.sources.source import Source
from propsd.enums import SourceStatus, SourceEvents
from propsd.sources.consul.parser import ConsulParser


@SourceFactory('consul')
class ConsulSource(Source):
    _logger: logging.Logger = logging.getLogger(__name__)
    _parser: ConsulParser = ConsulParser()

    def __init__(self, name, opts: Optional[dict] = None):
        default_options = {
            'host': settings.get('consul.host'),
            'port': settings.get('consul.port'),
            'scheme': settings.get('consul.scheme')
        }
        options = {**default_options, **opts} if opts else default_options

        super().__init__(name, 1, options)

        self._client = consul.Consul(**options)
        self._catalog = consul.Consul.Catalog(self._client)
        self._health = consul.Consul.Health(self._client)

    def _get(self):
        raw_data = {}
        try:
            services = self._catalog.services(consistency='stale')
        except (consul.ConsulException, ConnectionError) as ex:
            self._logger.error('Source/Consul: Caught the following error: %s', ex)
            self._status = SourceStatus.ERROR
            return None
        for service in services[1]:
            service_data = self._health.service(service, passing=True)
            raw_data[service] = service_data[1]

        self._status = SourceStatus.OK
        properties = self._parser.parse(raw_data)
        self._send_event(SourceEvents.UPDATE, source=self, data=properties)
        self.properties = properties
