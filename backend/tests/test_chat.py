from unittest.mock import patch
import litellm
from litellm.utils import ModelResponse, Choices, Message, Usage


def make_mock_response(content: str, prompt_tokens: int = 15, completion_tokens: int = 8):
    resp = ModelResponse()
    resp.choices = [Choices(message=Message(content=content, role="assistant"))]
    resp.usage = Usage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
    )
    resp._hidden_params = {"cache_hit": False}
    return resp


@patch("litellm.acompletion")
def test_chat_happy_path(mock_acompletion, client):
    mock_acompletion.return_value = make_mock_response("The capital of France is Paris.", 42, 9)

    response = client.post(
        "/chat",
        json={"session_id": "session-happy-1", "message": "What is the capital of France?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "session-happy-1"
    assert data["reply"] == "The capital of France is Paris."

    meta = data["metadata"]
    assert meta["resolution_source"] == "LIVE_INFERENCE"
    assert meta["model"] == "gemini/gemini-2.0-flash"
    assert meta["key_id"] == "key_1"
    assert meta["fallback_attempts"] == 0
    assert meta["input_tokens"] == 42
    assert meta["output_tokens"] == 9
    assert isinstance(meta["latency_ms"], int)
    assert meta["latency_ms"] >= 1
