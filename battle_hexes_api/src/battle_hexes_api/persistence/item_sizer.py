"""Deterministic sizing for the provider-neutral in-memory adapter."""

from collections.abc import Mapping


class InMemoryItemSizer:
    """Measure a logical item using its UTF-8 and binary payload size."""

    def size_bytes(self, item):
        return self._size(item)

    def _size(self, value):
        if isinstance(value, Mapping):
            return sum(
                len(str(key).encode("utf-8")) + self._size(child)
                for key, child in value.items()
            )
        if isinstance(value, bytes):
            return len(value)
        if isinstance(value, str):
            return len(value.encode("utf-8"))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return len(str(value).encode("ascii"))
        if isinstance(value, bool):
            return 1
        if value is None:
            return 1
        if isinstance(value, (list, tuple)):
            return sum(self._size(child) for child in value)
        raise TypeError(f"unsupported item value: {type(value).__name__}")
