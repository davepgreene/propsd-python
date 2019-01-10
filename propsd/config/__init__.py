import json
from typing import Optional

import toml
import yaml
from boltons.timeutils import parse_timedelta
from configobj import ConfigObj, ConfigObjError
from dynaconf import settings as dc_settings, loaders, constants as ct

from propsd.config.default import *  # noqa pylint: disable=wildcard-import
from propsd.util import called

settings = dc_settings
settings.MERGE_ENABLED_FOR_DYNACONF = True


settings.set('_configured', lambda: load_default_settings.has_been_called and load_default_settings.has_been_called)


def unbox_settings_object(key):
    # If the properties key exists we have to unbox the value
    obj = settings.get(key, {})
    return obj.to_dict() if obj else obj


def to_seconds(duration: Optional[str]) -> Optional[int]:
    return parse_timedelta(duration).seconds if duration else None


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
