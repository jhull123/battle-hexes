"""Validation and deterministic identity utilities for API commands."""

import hashlib
import json
import math
import re

from .contracts import CommandIdentity


_PERCENT_OCTET = re.compile(r"%([0-9a-fA-F]{2})")
_HTTP_TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


def digest_idempotency_key(key):
    """Validate a client key and return only its SHA-256 digest."""
    if not isinstance(key, str):
        raise ValueError("idempotency key must be a string")
    try:
        encoded = key.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("idempotency key must contain only ASCII") from error
    if not 1 <= len(key) <= 255:
        raise ValueError(
            "idempotency key must contain 1 through 255 characters"
        )
    if any(
        character.isspace()
        or ord(character) < 32
        or ord(character) == 127
        for character in key
    ):
        raise ValueError(
            "idempotency key must not contain whitespace or control characters"
        )
    return hashlib.sha256(encoded).hexdigest()


def normalize_method(method):
    """Validate and uppercase an HTTP method token."""
    if not isinstance(method, str) or not _HTTP_TOKEN.fullmatch(method):
        raise ValueError("method must be a valid HTTP token")
    return method.upper()


def normalize_route(route):
    """Normalize only the route variations permitted by the contract."""
    if (
        not isinstance(route, str)
        or not route.startswith("/")
        or route.startswith("//")
    ):
        raise ValueError("route must be an absolute path without an authority")
    if "?" in route or "#" in route:
        raise ValueError("route must not include a query or fragment")
    index = 0
    while index < len(route):
        if route[index] == "%":
            if not _PERCENT_OCTET.match(route, index):
                raise ValueError(
                    "route contains an invalid percent-encoded octet"
                )
            index += 3
        else:
            index += 1
    normalized = _PERCENT_OCTET.sub(
        lambda match: "%" + match.group(1).upper(), route
    )
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized


def _validate_json(value, seen):
    if isinstance(value, str):
        _require_utf8(value, "JSON strings")
        return
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return
    if isinstance(value, list):
        identity = id(value)
        if identity in seen:
            raise ValueError("JSON values must not contain cycles")
        seen.add(identity)
        try:
            for item in value:
                _validate_json(item, seen)
        finally:
            seen.remove(identity)
        return
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        for key in value:
            _require_utf8(key, "JSON object keys")
        identity = id(value)
        if identity in seen:
            raise ValueError("JSON values must not contain cycles")
        seen.add(identity)
        try:
            for item in value.values():
                _validate_json(item, seen)
        finally:
            seen.remove(identity)
        return
    raise ValueError("body must contain only JSON-compatible values")


def _require_utf8(value, description):
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError(f"{description} must be valid Unicode") from error


def canonical_json_bytes(value):
    """Encode a validated JSON-compatible value deterministically."""
    _validate_json(value, set())
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def fingerprint_request(method, route, expected_version, body=None):
    """Return the digest of the canonical four-field command document."""
    if expected_version is not None and (
        isinstance(expected_version, bool)
        or not isinstance(expected_version, int)
        or expected_version < 1
    ):
        raise ValueError("expected_version must be a positive integer or None")
    document = {
        "body": body,
        "expectedGameVersion": expected_version,
        "method": normalize_method(method),
        "route": normalize_route(route),
    }
    return hashlib.sha256(canonical_json_bytes(document)).hexdigest()


def create_command_identity(key, method, route, expected_version, body=None):
    """Construct a command identity without retaining the raw client key."""
    return CommandIdentity(
        key_digest=digest_idempotency_key(key),
        request_fingerprint=fingerprint_request(
            method, route, expected_version, body
        ),
    )
