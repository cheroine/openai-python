"""Helpers for working with reasoning items returned by the Responses API."""

from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping, MutableSequence, Optional, TypeVar, Union, cast

from .._compat import model_copy, model_parse
from .._models import BaseModel
from ..types.responses.response import Response
from ..types.responses.parsed_response import ParsedResponse
from ..types.responses.response_reasoning_item import ResponseReasoningItem, Content as ReasoningContent

__all__ = ["ReasoningDecryptor", "decrypt_reasoning_items"]

ReasoningContentLike = Union[ReasoningContent, Mapping[str, object]]
"""Type accepted from a decryptor when populating reasoning content."""

ReasoningDecryptor = Callable[[str], Optional[Iterable[ReasoningContentLike]]]
"""Callback that decrypts the ``encrypted_content`` field on a reasoning item."""

_ResponseT = TypeVar("_ResponseT", Response, ParsedResponse[Any])
_OutputItemT = TypeVar("_OutputItemT", bound=BaseModel)


def decrypt_reasoning_items(response: _ResponseT, *, decrypt: ReasoningDecryptor) -> _ResponseT:
    """Populate reasoning output items with decrypted content.

    The Responses API can return reasoning outputs with the ``encrypted_content`` field
    populated when ``reasoning.encrypted_content`` is included in the ``include``
    parameter. This helper walks every output item on ``response`` and, when possible,
    replaces the encrypted reasoning payload with the decrypted content produced by the
    supplied ``decrypt`` callback.

    The original ``response`` instance is never mutated. If no reasoning outputs were
    updated the input object is returned unchanged.
    """

    updated_output: MutableSequence[BaseModel] = []
    changed = False

    for item in response.output:
        new_item = _decrypt_output_item(item, decrypt)
        if new_item is not item:
            changed = True
        updated_output.append(new_item)

    if not changed:
        return response

    clone = model_copy(response, deep=True)
    clone.output = list(updated_output)  # type: ignore[assignment]
    return clone


def _decrypt_output_item(item: _OutputItemT, decrypt: ReasoningDecryptor) -> _OutputItemT:
    if not isinstance(item, ResponseReasoningItem):
        return item

    return cast(_OutputItemT, _decrypt_reasoning_item(item, decrypt))


def _decrypt_reasoning_item(item: ResponseReasoningItem, decrypt: ReasoningDecryptor) -> ResponseReasoningItem:
    if item.content:
        return item

    encrypted = item.encrypted_content
    if not encrypted:
        return item

    decrypted = decrypt(encrypted)
    if decrypted is None:
        return item

    content = _normalise_reasoning_content(decrypted)

    new_item = model_copy(item, deep=True)
    new_item.content = content
    return new_item


def _normalise_reasoning_content(values: Iterable[ReasoningContentLike]) -> list[ReasoningContent]:
    content: list[ReasoningContent] = []
    for value in values:
        if isinstance(value, ReasoningContent):
            content.append(value)
        else:
            content.append(model_parse(ReasoningContent, value))

    return content
