import logging
from typing import TYPE_CHECKING, List

from quart import jsonify, abort

from propsd.sourcemanager import SourceManager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from quart import Response  # pylint: disable=ungrouped-imports


async def properties() -> 'Response':
    return jsonify(SourceManager.properties())


async def nested_properties(subpath) -> 'Response':
    logger.debug('API/Properties: Received sub-path %s', subpath)
    props = SourceManager.properties()
    paths: List[str] = list(filter(None, subpath.split('/')))
    paths.reverse()
    while paths:
        path = paths.pop()
        if path not in props:
            abort(404)
        props = props.get(path)  # type: ignore
    return jsonify(props)
