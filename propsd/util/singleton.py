import functools
import threading
from typing import Any, Type, Dict

_lock = threading.Lock()


def _synchronized(lock):
    def wrapper(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            with lock:
                return fn(*args, **kwargs)
        return wrapped
    return wrapper


class Singleton(type):
    _instances: Dict['Singleton', Any] = {}

    @_synchronized(_lock)
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
