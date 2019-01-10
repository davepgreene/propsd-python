import base64
import hashlib
import logging
import time
from collections import deque
from typing import Optional

import boto3
import requests
from botocore.exceptions import ClientError

from propsd.config import settings
from propsd.enums import SourceEvents, SourceStatus
from propsd.sources.factory import SourceFactory
from propsd.sources.metadata.parser import mappings, MetadataParser
from propsd.sources.source import Source


@SourceFactory('ec2-metadata')
class MetadataSource(Source):
    # pylint: disable=invalid-name
    VERSION = 'latest'
    DEFAULT_TIMEOUT = 5  # in seconds
    DEFAULT_HOST = '169.254.169.254'
    # pylint: enable=invalid-name
    _logger: logging.Logger = logging.getLogger(__name__)
    _parser: MetadataParser = MetadataParser()

    def __init__(self, opts: Optional[dict] = None):
        super().__init__('ec2-metadata', 1, opts)
        self._host = settings.get('metadata.host') if settings.get('metadata.host') else self.DEFAULT_TIMEOUT
        self._timeout = settings.get('metadata.timeout') if settings.get('metadata.timeout') else self.DEFAULT_TIMEOUT

    def _get_autoscaling_group(self, region: str, instance_id: str) -> Optional[str]:
        self._logger.debug('Source/Metadata: Retrieving auto-scaling-group data')
        autoscaling = boto3.client('autoscaling', region_name=region)
        try:
            asg = [i.get('AutoScalingGroupName') for i in autoscaling.describe_auto_scaling_instances(
                InstanceIds=[instance_id]
            ).get('AutoScalingInstances')]
        except ClientError:
            asg = [None]

        # No reason it should be longer than 1 but worth a check
        if len(asg) > 1:  # pylint: disable=len-as-condition
            self._logger.warning('Source/Metadata: Instance id %s is in multiple auto-scaling groups', instance_id)
        return asg[0]

    def _get_meta_data(self):
        url_base = 'http://{}/{}'.format(self._host, self.VERSION)
        paths = deque(mappings.keys())
        results = {}

        while paths:
            path = paths.pop()
            joined_path = '{}/{}'.format(url_base, path)
            res = requests.get(joined_path)
            if res.status_code != 200:
                self._logger.debug('Source/Metadata: Unable to retrieve metadata from %s. Got HTTP status code %d',
                                   path,
                                   res.status_code)
                continue
            if path.endswith('/'):
                items = res.text.strip().split('\n')
                for item in items:
                    paths.append('{}{}'.format(path, item))
            else:
                results[path] = res.text
        return results

    def _get(self) -> None:
        timer = time.time()
        properties = self._parser.parse(self._get_meta_data())

        instance_id = properties.get('meta-data/instance-id')
        availability_zone = properties.get('meta-data/placement/availability-zone')
        if instance_id and availability_zone:
            region = availability_zone[:-1]

            if not self.properties.get('auto-scaling-group'):
                properties['auto-scaling-group'] = self._get_autoscaling_group(region, instance_id)
            else:
                self._logger.debug('Source/Metadata: Using cached auto-scaling-group data.')
                properties['auto-scaling-group'] = self.properties.get('auto-scaling-group')

        sha1 = hashlib.sha1()
        paths = properties.keys()

        self._logger.debug('Source/Metadata: Fetched %d paths from the ec2-metadata service', len(paths),
                           extra={'status': self.status()})
        for path in sorted(paths):
            sha1.update(path.encode('utf-8'))
        signature = base64.b64encode(sha1.digest())

        self._logger.debug('Source/Metadata: Polled %s source %s in %dms',
                           self.__class__.__name__, self.name, time.time() - timer,
                           extra={'status': self.status()})

        if self._signature == signature:
            self._status = SourceStatus.NO_UPDATE
            self._send_event(SourceEvents.NO_UPDATE, source=self)
            return

        self._status = SourceStatus.OK
        self._signature = signature
        self._send_event(SourceEvents.UPDATE, source=self, data=properties)
        self.properties = properties
