from unittest.mock import patch
import litellm
from litellm.utils import ModelResponse, Choices, Message, Usage
from litellm.exceptions import RateLimitError


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
def test_simulate_failure_key_1_429(mock_acompletion, client):
    mock_acompletion.return_value = make_mock_response("Failover succeeded to key_2", 20, 5)

    response = client.post(
        "/chat",
        json={"session_id": "failover-sess-1", "message": "Testing failover"},
        headers={"X-Simulate-Failure": "key_1=429"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["resolution_source"] == "LIVE_INFERENCE"
    assert data["metadata"]["key_id"] == "key_2"
    assert data["metadata"]["fallback_attempts"] == 1


@patch("litellm.acompletion")
def test_simulate_failure_key_1_500(mock_acompletion, client):
    mock_acompletion.return_value = make_mock_response("Failover succeeded on 500", 20, 5)

    response = client.post(
        "/chat",
        json={"session_id": "failover-sess-2", "message": "Testing 500 failover"},
        headers={"X-Simulate-Failure": "key_1=500"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["key_id"] == "key_2"
    assert data["metadata"]["fallback_attempts"] == 1


@patch("litellm.acompletion")
def test_simulate_failure_all_keys(mock_acompletion, client):
    response = client.post(
        "/chat",
        json={"session_id": "failover-sess-all", "message": "All keys down"},
        headers={"X-Simulate-Failure": "*=429"},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "all providers unavailable"}

    # Ensure nothing was saved to DB for this session
    msg_res = client.get("/sessions/failover-sess-all/messages")
    assert msg_res.status_code == 404


@patch("litellm.acompletion")
def test_request_scoped_simulation_isolation(mock_acompletion, client):
    # After a simulated failure, a subsequent request without headers succeeds on key_1
    mock_acompletion.return_value = make_mock_response("Back to normal", 18, 4)

    response = client.post(
        "/chat",
        json={"session_id": "normal-sess", "message": "Normal request"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["key_id"] == "key_1"
    assert data["metadata"]["fallback_attempts"] == 0


@patch("litellm.acompletion")
def test_real_provider_rate_limit_exception(mock_acompletion, client):
    mock_acompletion.side_effect = [
        RateLimitError(
            message="Rate limit exceeded",
            model="gemini/gemini-2.0-flash",
            llm_provider="gemini",
        ),
        make_mock_response("Succeeded via real failover", 22, 6),
    ]

    response = client.post(
        "/chat",
        json={"session_id": "real-ratelimit-sess", "message": "Testing real exception"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["key_id"] == "key_2"
    assert data["metadata"]["fallback_attempts"] == 1


@patch("litellm.acompletion")
def test_simulation_disabled_switch(mock_acompletion, client):
    from app.config import settings
    settings.ENABLE_FAILURE_SIMULATION = False
    try:
        mock_acompletion.return_value = make_mock_response("Simulation ignored", 12, 3)
        response = client.post(
            "/chat",
            json={"session_id": "sim-disabled-sess", "message": "Test disabled"},
            headers={"X-Simulate-Failure": "*=429"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["key_id"] == "key_1"
        assert data["metadata"]["fallback_attempts"] == 0
    finally:
        settings.ENABLE_FAILURE_SIMULATION = True
