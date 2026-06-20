"""Shared Pydantic base classes for API schemas."""

from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    """Convert a snake_case field name to lower camelCase."""

    words = value.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


def to_snake(value: str) -> str:
    """Convert a lower camelCase field name to snake_case."""

    output = []
    for character in value:
        if character.isupper():
            output.append("_")
            output.append(character.lower())
        else:
            output.append(character)
    return "".join(output)


class ApiBaseModel(BaseModel):
    """Base model that exposes camelCase JSON aliases for API payloads."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
