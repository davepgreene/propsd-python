from dynaconf import settings as dc_settings, loaders, constants as ct
import yaml
import json
import toml
from configobj import ConfigObj, ConfigObjError
from propsd.config.default import *

settings = dc_settings
settings.MERGE_ENABLED_FOR_DYNACONF = True


def load_user_settings(path):
    loaders = [
        {'ext': ct.YAML_EXTENSIONS, 'name': 'YAML', 'loader': _load_yaml},
        {'ext': ct.TOML_EXTENSIONS, 'name': 'TOML', 'loader': _load_toml},
        {'ext': ct.INI_EXTENSIONS, 'name': 'INI', 'loader': _load_ini},
        {'ext': ct.JSON_EXTENSIONS, 'name': 'JSON', 'loader': _load_json},
    ]
    conf = next(loader['loader'](path) for loader in loaders if path.endswith(loader['ext']))

    for k, v in conf.items():
        settings.set(k, v)


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
