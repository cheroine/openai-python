from __future__ import annotations

import base64
import copy
import json
from typing import Iterable, Mapping

import pytest

from openai.lib.reasoning import decrypt_reasoning_items
from openai.types.responses.response import Response
from openai.types.responses.parsed_response import ParsedResponse
from openai.types.responses.response_reasoning_item import Content as ReasoningContent


def _encode_reasoning_content(entries: Iterable[Mapping[str, object]]) -> str:
    return base64.b64encode(json.dumps(list(entries)).encode("utf-8")).decode("ascii")


SAMPLE_CONTENT = [
    {"type": "reasoning_text", "text": "first"},
    {"type": "reasoning_text", "text": "second"},
]
SAMPLE_ENCRYPTED = _encode_reasoning_content(SAMPLE_CONTENT)


def _response_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": "resp_123",
        "created_at": 42,
        "model": "gpt-4o-mini",
        "object": "response",
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": [],
        "output": [
            {
                "id": "reasoning_1",
                "type": "reasoning",
                "status": "completed",
                "summary": [{"type": "summary_text", "text": "summary"}],
                "encrypted_content": SAMPLE_ENCRYPTED,
            }
        ],
    }

    payload.update(overrides)
    return payload


def _simple_decryptor(value: str):
    return json.loads(base64.b64decode(value))


def test_decrypts_reasoning_items_without_mutating_original() -> None:
    response = Response.model_validate(_response_payload())

    decrypted = decrypt_reasoning_items(response, decrypt=_simple_decryptor)

    assert decrypted is not response
    reasoning = decrypted.output[0]
    assert reasoning.type == "reasoning"
    assert reasoning.content is not None
    assert [part.text for part in reasoning.content] == ["first", "second"]
    # original response remains unchanged
    assert response.output[0].content is None


def test_works_with_parsed_response_instances() -> None:
    parsed = ParsedResponse[None].model_validate(_response_payload())

    result = decrypt_reasoning_items(parsed, decrypt=_simple_decryptor)

    assert isinstance(result, ParsedResponse)
    assert result.output[0].content is not None
    assert result.output[0].content[0].text == "first"


def test_skips_items_without_encrypted_content() -> None:
    payload = _response_payload()
    output = copy.deepcopy(payload["output"])  # type: ignore[index]
    output[0].pop("encrypted_content")  # type: ignore[index]
    payload["output"] = output

    response = Response.model_validate(payload)

    def _failing_decrypt(_: str):
        pytest.fail("decrypt should not be called when no encrypted content exists")

    assert decrypt_reasoning_items(response, decrypt=_failing_decrypt) is response


def test_accepts_prebuilt_reasoning_content_objects() -> None:
    response = Response.model_validate(_response_payload())
    content_obj = ReasoningContent(type="reasoning_text", text="ready")

    def _custom_decrypt(_: str) -> list[ReasoningContent]:
        return [content_obj]

    decrypted = decrypt_reasoning_items(response, decrypt=_custom_decrypt)

    assert decrypted.output[0].content is not None
    assert decrypted.output[0].content[0].text == "ready"
