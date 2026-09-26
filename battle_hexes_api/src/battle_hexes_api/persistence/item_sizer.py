"""Deterministic item sizing for the provider-neutral in-memory adapter."""

from collections.abc import Mapping


class InMemoryItemSizer:
    """Estimate item size using DynamoDB attribute and collection rules."""

    def size_bytes(self, item):
        if not isinstance(item, Mapping):
            raise TypeError("item must be a mapping")
        return self._mapping_size(item)

    def _mapping_size(self, value):
        return sum(
            len(str(key).encode("utf-8")) + self._size(child)
            for key, child in value.items()
        )

    def _size(self, value):
        if isinstance(value, Mapping):
            return 3 + len(value) + self._mapping_size(value)
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
            return 3 + len(value) + sum(self._size(child) for child in value)
        raise TypeError(f"unsupported item value: {type(value).__name__}")
