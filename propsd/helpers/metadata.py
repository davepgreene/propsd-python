import json
import sys
from pathlib import Path

import click
from quart import Quart, abort, Response

app = Quart(__name__)

not_found_body = """
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
    <head>
        <title>404 - Not Found</title>
    </head>
    <body>
        <h1>404 - Not Found</h1>
    </body>
</html>
"""


@click.command()
@click.option('--data', '-d', type=click.Path(dir_okay=False, resolve_path=True),
              default=Path(__file__).parent / 'mock-metadata-paths.json',
              help='Path to path config')
@click.option('--host', '-h', default='127.0.0.1', help='The host to broadcast on')
@click.option('--port', '-p', default=8080, help='The port to run on')
def metadata(data, host, port):
    if data is None:
        sys.exit(1)

    with open(data) as file:
        paths = json.load(file)
    app.config.update(PATHS=paths)
    app.run(host=host, port=port)


@app.route('/', methods=['GET'])
async def root():
    return _get_path_data('/')


@app.route('/<path:subpath>', methods=['GET'])
async def metadata_route(subpath):
    if subpath in ['latest', 'latest/']:
        return _latest()
    return _get_path_data('/{}'.format(subpath))


def _latest():
    latest = ['{}/\n'.format(l) for l in _get_sub_paths('/latest')]
    return Response(''.join(latest), mimetype='text/plain')


def _get_sub_paths(prefix):
    paths = app.config.get('PATHS')
    accumulator = []
    for path in paths:
        if path.startswith(prefix):
            path = path[len(prefix):]
            sub_paths = list(filter(None, path.split('/')))
            if len(sub_paths) == 1:
                accumulator.append('/'.join(sub_paths))
    return accumulator


def _get_path_data(path):
    paths = app.config.get('PATHS')
    if path not in paths.keys():
        sub_paths = _get_sub_paths(path)
        if not sub_paths:
            abort(404)
        else:
            return Response(''.join(['{}/\n'.format(s) for s in sub_paths]), mimetype='text/plain')
    return Response(paths.get(path), mimetype='text/plain')


@app.errorhandler(404)
async def not_found(err):  # pylint: disable=unused-argument
    return Response(not_found_body, 404, mimetype='text/html')
