from unittest.mock import patch
import litellm
from litellm.utils import ModelResponse, Choices, Message, Usage


def make_mock_response(content: str, prompt_tokens: int = 20, completion_tokens: int = 10):
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
def test_cross_session_cache_hit(mock_acompletion, client):
    mock_acompletion.return_value = make_mock_response("Paris is the capital.", 25, 6)

    # 1. Turn in session A (Live Inference)
    res_a = client.post(
        "/chat",
        json={"session_id": "cache-sess-A", "message": "What is the capital of France?"},
    )
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert data_a["metadata"]["key_id"] == "key_1"

    # 2. Same first message in brand-new session B (LLM_CACHE)
    res_b = client.post(
        "/chat",
        json={"session_id": "cache-sess-B", "message": "What is the capital of France?"},
    )
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["reply"] == data_a["reply"]
    assert data_b["metadata"]["resolution_source"] == "LLM_CACHE"
    assert data_b["metadata"]["key_id"] is None
    assert data_b["metadata"]["fallback_attempts"] == 0
    assert data_b["metadata"]["input_tokens"] == data_a["metadata"]["input_tokens"]
    assert data_b["metadata"]["output_tokens"] == data_a["metadata"]["output_tokens"]

    # 3. Different message in session C (LIVE_INFERENCE)
    mock_acompletion.return_value = make_mock_response("Rome is the capital.", 22, 5)
    res_c = client.post(
        "/chat",
        json={"session_id": "cache-sess-C", "message": "What is the capital of Italy?"},
    )
    assert res_c.status_code == 200
    data_c = res_c.json()
    assert data_c["metadata"]["resolution_source"] == "LIVE_INFERENCE"


@patch("litellm.acompletion")
def test_system_prompt_cache_isolation(mock_acompletion, client):
    mock_acompletion.return_value = make_mock_response("Bonjour Paris", 30, 4)

    # Message with custom system prompt should miss default cache
    res = client.post(
        "/chat",
        json={
            "session_id": "sys-prompt-sess",
            "message": "What is the capital of France?",
            "system_prompt": "Answer in French only.",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["metadata"]["resolution_source"] == "LIVE_INFERENCE"
