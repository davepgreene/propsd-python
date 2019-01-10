import functools
import time
from typing import Match


def called(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        wrapper.has_been_called = True
        return func(*args, **kwargs)
    wrapper.has_been_called = False
    return wrapper


def debounce(seconds: int):
    def wrapper(func):
        first_execution = None

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            nonlocal first_execution
            current_time = time.time()
            if first_execution is None or current_time - first_execution >= seconds:
                result = func(*args, **kwargs)
                first_execution = time.time()
                return result
            return None
        return wrapped
    return wrapper


def convert_to_object_access(match: Match) -> str:
    filters = match.group(1).split('|')
    if len(filters) > 1:
        segments = filters.pop(0).split(':')
    else:
        filters = None
        segments = match.group(1).split(':')
    head = [segments.pop(0)] + ["['{}']".format(s) for s in segments]
    if filters:
        return '{{{{ {0}|{1} }}}}'.format(''.join(head), '|'.join(filters))
    else:
        return '{{{{ {0} }}}}'.format(''.join(head))
