"""Response validation, header canonicalization, and receipt replay."""

from typing import Mapping

from .command_models import SuccessfulResponse


_TRANSPORT_HEADERS = frozenset({"content-length", "date", "server"})


class CommandResponseFinalizer:
    """Finalize response data before it becomes an immutable receipt."""

    def finalize(self, value, version):
        """Validate serializer output and attach the resulting game version."""
        status, body, content_type, headers = self._response_fields(
            value, version
        )
        self._validate_success(status, body, content_type)
        return SuccessfulResponse(
            status,
            body,
            content_type,
            self._canonical_headers(headers, content_type, version),
            version,
        )

    @staticmethod
    def from_receipt(receipt):
        """Return the exact durable response represented by *receipt*."""
        return SuccessfulResponse(
            receipt.status_code,
            receipt.response_body,
            receipt.content_type,
            receipt.response_headers,
            receipt.game_version,
        )

    @staticmethod
    def _response_fields(value, version):
        if isinstance(value, SuccessfulResponse):
            if value.game_version != version:
                raise ValueError(
                    "serialized response has the wrong game version"
                )
            return (
                value.status_code,
                value.body,
                value.content_type,
                value.headers,
            )
        if isinstance(value, tuple) and len(value) == 4:
            return value
        try:
            return (
                value.status_code,
                value.body,
                value.content_type,
                value.headers,
            )
        except AttributeError as error:
            raise ValueError(
                "serializer returned an invalid response"
            ) from error

    @staticmethod
    def _validate_success(status, body, content_type):
        if (
            isinstance(status, bool)
            or not isinstance(status, int)
            or not 200 <= status <= 299
        ):
            raise ValueError(
                "successful status_code must be in the 2xx range"
            )
        if not isinstance(body, bytes):
            raise ValueError("serialized response body must be bytes")
        if not isinstance(content_type, str) or not content_type:
            raise ValueError("content_type must be a non-empty string")

    @staticmethod
    def _canonical_headers(headers, content_type, version):
        if not isinstance(headers, Mapping):
            raise ValueError("response headers must be a mapping")
        canonical = {}
        seen = set()
        for name, value in headers.items():
            if (
                not isinstance(name, str)
                or not name
                or not isinstance(value, str)
            ):
                raise ValueError("response headers must contain strings")
            lowered = name.lower()
            if lowered in seen:
                raise ValueError("response header names must be unique")
            seen.add(lowered)
            if lowered in _TRANSPORT_HEADERS or lowered == "content-type":
                continue
            canonical_name = "-".join(
                part.capitalize() for part in lowered.split("-")
            )
            canonical[canonical_name] = value
        expected = str(version)
        supplied = canonical.get("Game-Version")
        if supplied is not None and supplied != expected:
            raise ValueError("Game-Version does not match resulting version")
        canonical["Game-Version"] = expected
        return canonical
