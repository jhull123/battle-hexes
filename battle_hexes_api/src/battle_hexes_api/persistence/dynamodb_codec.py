"""DynamoDB item mapping for provider-neutral persistence values."""

from .contracts import CommandIdentity, CommandReceipt, StoredGame
from .errors import PersistenceUnavailableError


def game_key(game_id):
    return {"pk": {"S": f"GAME#{game_id}"}, "sk": {"S": "SNAPSHOT"}}


def receipt_key(key_digest):
    return {
        "pk": {"S": f"IDEMPOTENCY#{key_digest}"},
        "sk": {"S": "RECEIPT"},
    }


def encode_game(game):
    return {
        **game_key(game.game_id),
        "item_type": {"S": "game"},
        "game_id": {"S": game.game_id},
        "version": {"N": str(game.version)},
        "state_schema_version": {"N": str(game.state_schema_version)},
        "scenario_id": {"S": game.scenario_id},
        "scenario_version": {"S": game.scenario_version},
        "state": {"B": bytes(game.state)},
        "updated_at": {"N": str(game.updated_at)},
        "ttl": {"N": str(game.expires_at)},
    }


def encode_receipt(receipt):
    headers = {
        name: {"S": value}
        for name, value in receipt.response_headers.items()
    }
    return {
        **receipt_key(receipt.identity.key_digest),
        "item_type": {"S": "command_receipt"},
        "request_hash": {"S": receipt.identity.request_fingerprint},
        "game_id": {"S": receipt.game_id},
        "game_version": {"N": str(receipt.game_version)},
        "status_code": {"N": str(receipt.status_code)},
        "content_type": {"S": receipt.content_type},
        "response_body": {"B": bytes(receipt.response_body)},
        "response_headers": {"M": headers},
        "created_at": {"N": str(receipt.created_at)},
        "ttl": {"N": str(receipt.expires_at)},
    }


def decode_game(item, game_id):
    try:
        _require_key(item, game_key(game_id))
        if _string(item, "item_type") != "game":
            raise ValueError
        if _string(item, "game_id") != game_id:
            raise ValueError
        return StoredGame(
            game_id=game_id,
            version=_integer(item, "version"),
            state_schema_version=_integer(item, "state_schema_version"),
            scenario_id=_string(item, "scenario_id"),
            scenario_version=_string(item, "scenario_version"),
            state=_binary(item, "state"),
            updated_at=_integer(item, "updated_at"),
            expires_at=_integer(item, "ttl"),
        )
    except (KeyError, TypeError, ValueError, UnicodeError):
        raise PersistenceUnavailableError() from None


def decode_receipt(item, key_digest):
    try:
        _require_key(item, receipt_key(key_digest))
        if _string(item, "item_type") != "command_receipt":
            raise ValueError
        headers_value = item["response_headers"]
        if set(headers_value) != {"M"}:
            raise ValueError
        headers = {
            name: _attribute_string(value)
            for name, value in headers_value["M"].items()
        }
        return CommandReceipt(
            identity=CommandIdentity(
                key_digest=key_digest,
                request_fingerprint=_string(item, "request_hash"),
            ),
            game_id=_string(item, "game_id"),
            game_version=_integer(item, "game_version"),
            status_code=_integer(item, "status_code"),
            content_type=_string(item, "content_type"),
            response_body=_binary(item, "response_body"),
            response_headers=headers,
            created_at=_integer(item, "created_at"),
            expires_at=_integer(item, "ttl"),
        )
    except (KeyError, TypeError, ValueError, UnicodeError):
        raise PersistenceUnavailableError() from None


def _require_key(item, expected):
    if not isinstance(item, dict):
        raise TypeError
    if item.get("pk") != expected["pk"] or item.get("sk") != expected["sk"]:
        raise ValueError


def _string(item, name):
    return _attribute_string(item[name])


def _attribute_string(attribute):
    if not isinstance(attribute, dict) or set(attribute) != {"S"}:
        raise TypeError
    value = attribute["S"]
    if not isinstance(value, str):
        raise TypeError
    return value


def _integer(item, name):
    attribute = item[name]
    if not isinstance(attribute, dict) or set(attribute) != {"N"}:
        raise TypeError
    value = attribute["N"]
    if not isinstance(value, str) or not value.isascii():
        raise TypeError
    if not value.isdigit() or (len(value) > 1 and value.startswith("0")):
        raise ValueError
    return int(value)


def _binary(item, name):
    attribute = item[name]
    if not isinstance(attribute, dict) or set(attribute) != {"B"}:
        raise TypeError
    value = attribute["B"]
    if not isinstance(value, (bytes, bytearray)):
        raise TypeError
    return bytes(value)
