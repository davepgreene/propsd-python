#!/usr/bin/env python3

from os import environ
import click
from pathlib import Path
from flask import Flask
from dynaconf import FlaskDynaconf
from propsd.config import load_user_settings, load_default_settings, settings

load_default_settings()

app = Flask(__name__)
FlaskDynaconf(app)

ROOT = Path('/')
DEFAULT_CONFIG = ROOT / 'etc' / 'propsd' / 'config.json'
if not DEFAULT_CONFIG.exists():
    pass


def start(args):
    from meinheld import server
    host = args.host
    port = args.port

    server.listen((host, port))
    server.run(app)

@click.command()
@click.option('--config', '-c', type=click.Path(dir_okay=False, resolve_path=True),
              default=DEFAULT_CONFIG, help='Path to local propsd configuration')
@click.option('--colorize', is_flag=True, default=False, help='Colorize log output')
def propsd(config, colorize):
    load_user_settings(config)
    settings.set('colorize', colorize)
    click.echo(settings.get('log'))

    if environ.get('FLASK_DEBUG') != '1':
        pass
    #     start({})


if __name__ == '__main__':
    propsd()