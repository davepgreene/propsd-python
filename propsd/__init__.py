#!/usr/bin/env python3

import logging
from os import environ
from pathlib import Path

import click
from dynaconf import FlaskDynaconf
from quart import Quart

from propsd import constants
from propsd.api import v1
from propsd.config import load_user_settings, load_default_settings, settings, to_seconds, unbox_settings_object
from propsd.sourcemanager import SourceManager
from propsd.sources import *
from propsd.enums import SourceEvents, EnumEncoder, SourceState
from propsd.sources.factory import SourceFactory
from propsd.sources.schedulable import get_event

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] (%(levelname)s) %(name)s: %(message)s')
logger = logging.getLogger(__name__)

load_default_settings()

app = Quart(constants.APP_NAME, static_folder=None)
FlaskDynaconf(app)
app.json_encoder = EnumEncoder
app.register_blueprint(v1, url_prefix='/v1')

_required_initial_sources = [MetadataSource, TagsSource, KubernetesSource]
_loaded_initial_sources = []


@click.command()
@click.option('--configuration', '-c', type=click.Path(dir_okay=False, resolve_path=True),
              default=Path('/') / 'etc' / 'propsd' / 'config.json', help='Path to local propsd configuration')
@click.option('--colorize', is_flag=True, default=False, help='Colorize log output')
def propsd(configuration, colorize):
    # Load settings from file, cli flags, and environment
    load_user_settings(configuration)
    settings.set('colorize', colorize)
    settings.set('debug', environ.get('FLASK_DEBUG') == '1')
    logger.setLevel(settings.get('log.level').upper())

    logger.info('Propsd: Starting server')

    logger.info('Propsd: Beginning scheduling sources')
    # Load in properties from the config file
    config_properties = unbox_settings_object('properties')
    # Create the singleton instance of the SourceManager seeded with properties from the config file
    SourceManager(config_properties)

    # We need to make sure that both the tags and metadata sources have completed their first pass
    # before we load the index. Because these are special cases we can delay the index until they've
    # both fired their UPDATE event.
    def register_index(**kwargs):
        sender = kwargs.get('sender')
        source = kwargs.get('source')
        if sender in _required_initial_sources:
            _required_initial_sources.remove(sender)
            _loaded_initial_sources.append(source)

        if not _required_initial_sources:
            signal.disconnect(register_index, sender=MetadataSource)
            signal.disconnect(register_index, sender=TagsSource)
            signal.disconnect(register_index, sender=KubernetesSource)
            index_settings = unbox_settings_object('index')

            # Unschedule any initial sources that have been shutdown
            for s in _loaded_initial_sources:
                status = s.status()
                if status.get('state') == SourceState.SHUTDOWN:
                    SourceManager.unschedule(s)

            SourceManager.schedule(SourceFactory.new('s3-index')(opts=index_settings),
                                   index=True,
                                   delay=to_seconds(settings.get('index.interval')))

    signal = get_event(SourceEvents.UPDATE)
    signal.connect(register_index, sender=MetadataSource, weak=False)
    signal.connect(register_index, sender=TagsSource, weak=False)
    signal.connect(register_index, sender=KubernetesSource, weak=False)

    SourceManager.schedule(SourceFactory.new('ec2-metadata')(),
                           namespace='instance',
                           delay=to_seconds(settings.get('metadata.interval')))

    SourceManager.schedule(SourceFactory.new('ec2-tags')(),
                           namespace='instance:tags',
                           delay=to_seconds(settings.get('tags.interval')))

    SourceManager.schedule(SourceFactory.new('kubernetes')(),
                           namespace='instance:kubernetes',
                           delay=to_seconds(settings.get('kubernetes.interval')))

    SourceManager.start()

    host = settings.get('service.hostname')
    port = settings.get('service.port')
    logger.info('Propsd: starting server on %s:%d', host, port)
    app.run(host=host, port=port, debug=False, use_reloader=False)
