import sys
import json
from pathlib import Path
from quart import Quart, abort, Response
import click

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


@app.route('/<path:subpath>', methods=['GET'])
async def metadata_route(subpath):
    paths = app.config.get('PATHS')
    path = '/{}'.format(subpath)

    if path not in paths.keys():
        abort(404)
    return Response(paths.get(path), mimetype='text/plain')


@app.errorhandler(404)
async def not_found(err):  # pylint: disable=unused-argument
    return Response(not_found_body, 404, mimetype='text/html')
