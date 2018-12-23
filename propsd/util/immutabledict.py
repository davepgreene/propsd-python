from collections.abc import Mapping
from copy import deepcopy


class ImmutableDict(Mapping):
    __slots__ = '_store', '_hash'

    def __init__(self, *args, **kwargs):
        self._store = dict(*args, **kwargs)
        self._hash = None

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

    def update(self, *args, **kwargs):
        copy = deepcopy(self._store)
        copy.update(*args, **kwargs)
        return self.__class__(**copy)
