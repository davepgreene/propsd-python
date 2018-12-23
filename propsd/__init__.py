#!/usr/bin/env python3

from os import environ
import logging
from pathlib import Path

import click
from quart import Quart
from dynaconf import FlaskDynaconf
from propsd.config import load_user_settings, load_default_settings, settings, to_seconds
from propsd.api import v1
from propsd.sources.metadata import MetadataSource
from propsd.lib import Sources
from propsd import constants
from propsd.sources.source import SourceEvents, get_event
from propsd.sources.tags import TagsSource

settings.set('debug', environ.get('FLASK_DEBUG') == '1')

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] (%(levelname)s) %(name)s: %(message)s')
logger = logging.getLogger(constants.APP_NAME)

load_default_settings()

app = Quart(constants.APP_NAME, static_folder=None)
FlaskDynaconf(app)
app.register_blueprint(v1, url_prefix='/v1')


def register_initial_sources():
    from propsd.util.dispatch import receiver
    m = MetadataSource()
    t = TagsSource()

    def register_tags(**kwargs):
        pass

    def register_index(**kwargs):
        pass

    signal = get_event(SourceEvents.UPDATE)
    signal.connect(register_tags, sender=MetadataSource, weak=False)
    Sources().schedule(m, to_seconds(settings.get('metadata.interval')))
    Sources().schedule(t, to_seconds(settings.get('tags.interval')))


def start():
    from meinheld import server
    host = settings.get('service.hostname')
    port = settings.get('service.port')

    logger.info('Beginning scheduling')
    # Load in properties from the config file
    config_properties = settings.get('properties', {})
    if config_properties:
        # If the properties key exists we have to unbox the value
        config_properties = config_properties.to_dict()

    Sources(initial_properties=config_properties)

    register_initial_sources()
    Sources().start()

    if settings.DEBUG:
        app.run(host=host, port=port, debug=False, use_reloader=False)
    else:
        server.listen((host, port))
        server.run(app)


@click.command()
@click.option('--configuration', '-c', type=click.Path(dir_okay=False, resolve_path=True),
              default=Path('/') / 'etc' / 'propsd' / 'config.json', help='Path to local propsd configuration')
@click.option('--colorize', is_flag=True, default=False, help='Colorize log output')
def propsd(configuration, colorize):
    load_user_settings(configuration)
    settings.set('colorize', colorize)
    logger.setLevel(settings.get('log.level').upper())

    logger.info('Starting server')

    start()
