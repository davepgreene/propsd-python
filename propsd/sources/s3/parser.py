import json
import logging
from typing import Tuple, Optional

from botocore.response import StreamingBody
from jinja2 import Environment

from propsd.sources.parser import Parser

logger = logging.getLogger(__name__)


class S3Parser(Parser):
    def parse(self, data: StreamingBody) -> Tuple[Optional[int], dict, list]:
        body = data.read().decode('utf-8')
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            logger.warning('Source/S3/Parser: Unable to parse index body as JSON')
            return None, {}, []
        return body.get('version'), body.get('properties', {}), body.get('sources', [])
