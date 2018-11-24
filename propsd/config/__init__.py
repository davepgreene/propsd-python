from dynaconf import settings as dc_settings, loaders
from propsd.config.default import *

settings = dc_settings
settings.MERGE_ENABLED_FOR_DYNACONF = True


def load_user_settings(path):
    loaders.json_loader.load(settings, filename=path, silent=False)


def load_default_settings():
    loaders.py_loader.load(settings, 'propsd.config')
