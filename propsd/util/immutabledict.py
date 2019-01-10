from collections.abc import Mapping
from copy import deepcopy
from threading import Lock


class ImmutableDict(Mapping):
    __slots__ = '_store', '_hash', '_lock'

    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)
        self._hash = None
        self._lock = Lock()

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)

    def __getitem__(self, k):
        return self._store[k]

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, self._store)

    def __hash__(self):
        if self._hash is None:
            dict_hash = 0
            for key, value in self._store.items():
                dict_hash ^= hash((key, value))
            self._hash = dict_hash
        return self._hash

    def to_dict(self):
        return self._store

    def update(self, *args, **kwargs):
        copy = deepcopy(self._store)
        with self._lock:
            copy.update(*args, **kwargs)
        return self.__class__(**copy)
