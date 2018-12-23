import json
from datetime import timedelta
import durationpy
import yaml
import toml
from configobj import ConfigObj, ConfigObjError
from dynaconf import settings as dc_settings, loaders, constants as ct
from propsd.util import called
from propsd.config.default import *  # noqa pylint: disable=wildcard-import

settings = dc_settings
settings.MERGE_ENABLED_FOR_DYNACONF = True


settings.set('_configured', lambda: load_default_settings.has_been_called and load_default_settings.has_been_called)


def to_seconds(duration: str) -> int:
    return durationpy.from_str(duration).seconds


@called
def load_user_settings(path):
    settings_loaders = [
        {'ext': ct.YAML_EXTENSIONS, 'name': 'YAML', 'loader': _load_yaml},
        {'ext': ct.TOML_EXTENSIONS, 'name': 'TOML', 'loader': _load_toml},
        {'ext': ct.INI_EXTENSIONS, 'name': 'INI', 'loader': _load_ini},
        {'ext': ct.JSON_EXTENSIONS, 'name': 'JSON', 'loader': _load_json},
    ]
    conf = next(
        loader['loader'](path) for loader in settings_loaders if path.endswith(loader['ext'])
    )

    for key, value in conf.items():
        settings.set(key, value)


@called
def load_default_settings():
    loaders.py_loader.load(settings, 'propsd.config')


def _load_yaml(file):
    with open(file, 'r') as conf:
        try:
            return yaml.safe_load(conf)
        except yaml.YAMLError:
            return {}


def _load_json(file):
    with open(file, 'r') as conf:
        try:
            return json.load(conf)
        except json.JSONDecodeError:
            return {}


def _load_toml(file):
    try:
        return toml.load(file)
    except toml.TomlDecodeError:
        return {}


def _load_ini(file):
    with open(file, 'r') as conf:
        try:
            return ConfigObj(conf).dict()
        except ConfigObjError:
            return {}
