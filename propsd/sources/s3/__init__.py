import logging
from typing import Optional, List

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from propsd.config import settings
from propsd.enums import SourceStatus, SourceEvents
from propsd.sources.factory import SourceFactory
from propsd.sources.s3.parser import S3Parser
from propsd.sources.source import Source


@SourceFactory('s3')
class S3Source(Source):
    _version: Optional[int] = None
    _logger: logging.Logger = logging.getLogger(__name__)
    _response: Optional[dict] = None
    _sources: Optional[List[dict]] = None
    _parser: S3Parser = S3Parser()

    def __init__(self, name: str, instances: int = 1, opts: Optional[dict] = None):
        super().__init__(name, instances, opts)
        if not opts:
            opts = {}
        s3_opts = {}

        # If an endpoint is supplied in configuration we need to set a few special options
        endpoint = settings.get('index.endpoint')
        if endpoint:
            s3_opts['endpoint_url'] = endpoint
            s3_opts['use_ssl'] = False
            s3_opts['config'] = Config(s3={'addressing_style': 'path'})

        region = opts.get('region', 'us-east-1')
        self._bucket = opts.get('bucket')
        self._path = opts.get('path')

        if not self._bucket:
            raise AttributeError('Source/S3: Missing required parameter `bucket`!')
        if not self._path:
            raise AttributeError('Source/S3: Missing required parameter `path`!')

        self._client = boto3.client('s3', region, **s3_opts)

    def _get_object(self) -> Optional[dict]:
        req = {
            'Bucket': self._bucket,
            'Key': self._path
        }
        if self._signature:
            req['IfNoneMatch'] = self._signature

        try:
            obj = self._client.get_object(**req)
        except self._client.exceptions.NoSuchKey:
            self._logger.debug('Source/S3: Unable to retrieve source data. The key %s does not exist', req.get('Key'))
            self._status = SourceStatus.NO_EXIST
            return None
        except ClientError as ex:
            error_code = ex.response.get('Error', {}).get('Code')
            if error_code == 'NotModified':
                self._status = SourceStatus.NO_UPDATE
                self._send_event(SourceEvents.NO_UPDATE, source=self)
            else:
                self._logger.error('Source/S3: Caught the following `ClientError`: %s', str(ex))
            return None
        # `except`ing `ClientError` should cover the `IfNoneMatch` case but we should do an ETag comparison
        # just in case.
        etag = obj.get('ETag')
        if self._signature == etag:
            # No change
            self._status = SourceStatus.NO_UPDATE
            self._send_event(SourceEvents.NO_UPDATE, source=self)
            self._logger.debug('Source/S3: No change in %s/%s', self._bucket, self._path)
            return None

        self._status = SourceStatus.OK
        self._signature = etag
        return obj

    def _get(self):
        obj = self._get_object()
        if obj is None:
            return obj

        self._response = obj
        version, properties, sources = self._parser.parse(obj.get('Body'))
        self._version = version
        # Use the setter so it's wrapped in an ImmutableDict
        self._send_event(SourceEvents.UPDATE, source=self, data=properties)
        self.properties = properties
        self._sources = sources
        return obj
