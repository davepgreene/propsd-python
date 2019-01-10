from datetime import datetime
from http import HTTPStatus
from os import path

import pkg_resources
from quart import Blueprint, Response, jsonify, abort, request

from propsd import constants
from propsd.api.conqueso import conqueso, nested_conqueso
from propsd.api.properties import properties, nested_properties
from propsd.enums import SourceState
from propsd.sourcemanager import SourceManager

_api_version = 'v1'
v1 = Blueprint(_api_version, __name__)
v1.route('/properties', strict_slashes=False, methods=['GET', 'OPTIONS'])(properties)
v1.route('/properties/<path:subpath>')(nested_properties)
v1.route('/conqueso')(conqueso)
v1.route('/conqueso/api/roles/<path:role>/properties/<path:nested_property>')(nested_conqueso)

_started = datetime.now()
_healthy_states = [
    SourceState.RUNNING,
    SourceState.WAITING
]


def _get_version():
    return pkg_resources.require(constants.APP_NAME)[0].version


@v1.before_request
async def check_health():
    """
    Determine index health and respond if the index is either missing or not populated
    to protect against something querying Propsd before it's ready.
    """

    # We don't want to return the 404 for health and status routes
    if request.path in ['/{}'.format(path.join(_api_version, i)) for i in ['health', 'status']]:
        return

    healthy = False
    for index in SourceManager.health().get('indices', []):
        healthy = index.get('ok') and index.get('state') in _healthy_states
    if not healthy:
        abort(404)


@v1.errorhandler(HTTPStatus.NOT_FOUND)
async def not_found(err):  # pylint: disable=unused-argument
    return Response('{}', HTTPStatus.NOT_FOUND)


@v1.route('/health', methods=['GET'])
async def health():
    sources_health = SourceManager.health()
    code = sources_health.get('code', HTTPStatus.OK)
    plugins = {}

    for source in sources_health.get('sources', []):
        source_type = source.get('type')
        if source_type in plugins:
            plugins[source_type] += 1
        else:
            plugins[source_type] = 1
    resp = jsonify({
        'status': code,
        'uptime': (datetime.now() - _started).seconds,
        'plugins': plugins,
        'version': _get_version()
    })
    return resp, code


@v1.route('/status', methods=['GET'])
async def status():
    sources_health = SourceManager.health()
    code = sources_health.get('code', HTTPStatus.OK)

    sources = sources_health.get('sources', [])
    indices = sources_health.get('indices', [])

    resp = jsonify({
        'status': code,
        'uptime': (datetime.now() - _started).seconds,
        'version': _get_version(),
        'index': indices[0] if indices else None,
        'indices': indices,
        'sources': sources
    })
    return resp, code
