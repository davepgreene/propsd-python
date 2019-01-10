import base64
import hashlib
import json
import logging
from typing import Optional

import boto3
import requests

from propsd.config import settings
from propsd.enums import SourceEvents, SourceStatus
from propsd.sources.factory import SourceFactory
from propsd.sources.source import Source
from propsd.sources.tags.parser import TagsParser


@SourceFactory('ec2-tags')
class TagsSource(Source):
    # pylint: disable=invalid-name
    VERSION = 'latest'
    DEFAULT_TIMEOUT = 5  # in seconds
    DEFAULT_HOST = '169.254.169.254'
    # pylint: enable=invalid-name
    _logger: logging.Logger = logging.getLogger(__name__)
    _parser: TagsParser = TagsParser()

    def __init__(self, opts: Optional[dict] = None):
        super().__init__('ec2-tags', 1, opts)
        self._host = settings.get('metadata.host') if settings.get('metadata.host') else self.DEFAULT_TIMEOUT
        self._timeout = settings.get('metadata.timeout') if settings.get('metadata.timeout') else self.DEFAULT_TIMEOUT

    def _get_metadata_document(self):
        base_url = 'http://{}/{}'.format(self._host, self.VERSION)
        document_path = 'dynamic/instance-identity/document'
        res = requests.get('{}/{}'.format(base_url, document_path))
        if res.status_code != 200:
            self._logger.debug('Source/Tags: Unable to retrieve metadata from %s. Got HTTP status code %d',
                               document_path,
                               res.status_code)
            return {}
        return res.json()

    def _get(self) -> None:
        document = self._get_metadata_document()
        instance_id = document.get('instanceId')
        region = document.get('region')
        client = boto3.client('ec2', region_name=region)
        tags = client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [instance_id]}])
        tags = self._parser.parse(tags)
        sha1 = hashlib.sha1()

        self._logger.debug('Source/Tags: Fetched %d tags from the ec2 tags api', len(tags),
                           extra={'status': self.status()})

        for tag in sorted(tags):
            sha1.update(json.dumps(tag).encode('utf-8'))
        signature = base64.b64encode(sha1.digest())

        if self._signature == signature:
            self._status = SourceStatus.NO_UPDATE
            self._send_event(SourceEvents.NO_UPDATE, source=self)
            return

        self._status = SourceStatus.OK
        self._signature = signature
        self._send_event(SourceEvents.UPDATE, source=self, data=tags)
        self.properties = tags
