from typing import Optional
import logging
from collections import deque
import hashlib
import time
import base64
import requests
import boto3
from botocore.exceptions import ClientError
from propsd.sources.source import Source, SourceEvents
from propsd import constants
from propsd.config import settings
from propsd.sources.metadata.parser import mappings, MetadataParser

logger = logging.getLogger('{}.sources.metadata'.format(constants.APP_NAME))


class MetadataSource(Source):
    # pylint: disable=invalid-name
    VERSION = 'latest'
    DEFAULT_TIMEOUT = 5  # in seconds
    DEFAULT_HOST = '169.254.169.254'
    # pylint: enable=invalid-name

    def __init__(self, opts: Optional[object] = None):
        super().__init__('ec2-metadata', 1, opts)
        self._host = settings.get('metadata.host') if settings.get('metadata.host') else self.DEFAULT_TIMEOUT
        self._timeout = settings.get('metadata.timeout') if settings.get('metadata.timeout') else self.DEFAULT_TIMEOUT

    @staticmethod
    def _get_autoscaling_group(region: str, instance_id: str) -> Optional[str]:
        logger.debug('Retrieving auto-scaling-group data')
        autoscaling = boto3.client('autoscaling', region_name=region)
        try:
            asg = [i.get('AutoScalingGroupName') for i in autoscaling.describe_auto_scaling_instances(
                InstanceIds=[instance_id]
            ).get('AutoScalingInstances')]
        except ClientError:
            asg = [None]

        # No reason it should be longer than 1 but worth a check
        if len(asg) > 1:  # pylint: disable=len-as-condition
            logger.warning('Instance id %s is in multiple auto-scaling groups', instance_id)
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
                logger.debug('Unable to retrieve metadata from %s. Got HTTP status code %d', path,
                             res.status_code)
                continue
            if path.endswith('/'):
                items = res.text.strip().split('\n')
                for item in items:
                    paths.append('{}{}'.format(path, item))
            else:
                results[path] = res.text
        return results

    async def get(self) -> None:
        timer = time.time()
        properties = MetadataParser(self._get_meta_data()).parse()

        instance_id = properties.get('meta-data/instance-id')
        availability_zone = properties.get('meta-data/placement/availability-zone')
        if instance_id and availability_zone:
            region = availability_zone[:-1]

            if not self.properties.get('auto-scaling-group'):
                properties['auto-scaling-group'] = self._get_autoscaling_group(region, instance_id)
            else:
                logger.debug('Using cached auto-scaling-group data.')
                properties['auto-scaling-group'] = self.properties.get('auto-scaling-group')

        sha1 = hashlib.sha1()
        paths = properties.keys()

        logger.debug('Source/Metadata: Fetched %d paths from the ec2-metadata service', len(paths),
                     extra={'status': self.status()})
        for path in sorted(paths):
            sha1.update(path.encode('utf-8'))
        signature = base64.b64encode(sha1.digest())

        if self._state == signature:
            self._send_event(SourceEvents.NO_UPDATE, source=self)
        else:
            self._send_event(SourceEvents.UPDATE, source=self, data=properties)

        logger.debug('Source/Metadata: Polled %s source %s in %dms',
                     self.__class__.__name__, self.name, time.time() - timer,
                     extra={'status': self.status()})
        self._properties = properties

