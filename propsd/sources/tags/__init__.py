import logging
from typing import Optional

import boto3
import requests
from propsd.config import settings
from propsd import constants
from propsd.sources.source import Source

logger = logging.getLogger('{}.sources.tags'.format(constants.APP_NAME))


class TagsSource(Source):
    # pylint: disable=invalid-name
    VERSION = 'latest'
    DEFAULT_TIMEOUT = 5  # in seconds
    DEFAULT_HOST = '169.254.169.254'
    # pylint: enable=invalid-name

    def __init__(self, opts: Optional[object] = None):
        super().__init__('ec2-tags', 1, opts)
        self._host = settings.get('metadata.host') if settings.get('metadata.host') else self.DEFAULT_TIMEOUT
        self._timeout = settings.get('metadata.timeout') if settings.get('metadata.timeout') else self.DEFAULT_TIMEOUT

    def _get_metadata_document(self):
        base_url = 'http://{}/{}'.format(self._host, self.VERSION)
        document_path = 'dynamic/instance-identity/document'
        res = requests.get('{}/{}'.format(base_url, document_path))
        if res.status_code != 200:
            logger.debug('Unable to retrieve metadata from %s. Got HTTP status code %d', document_path, res.status_code)
            return {}
        document = res.json()

        instance_id = document.get('instanceId')
        region = document.get('region')
        client = boto3.client('ec2', region_name=region)
        tags = client.describe_tags(Filters=[{'Name': 'resource-id', 'Values': [instance_id]}])

        return tags

    async def get(self) -> None:
        data = self._get_metadata_document()
        pass
