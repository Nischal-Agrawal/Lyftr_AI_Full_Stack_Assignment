from unittest.mock import patch
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
def test_multi_turn_history_and_isolation(mock_acompletion, client):
    # Turn 1
    mock_acompletion.return_value = make_mock_response("Hello! How can I help?", 10, 6)
    client.post(
        "/chat",
        json={"session_id": "multi-sess-1", "message": "Hi, I am Alice"},
    )

    # Turn 2 in same session
    mock_acompletion.return_value = make_mock_response("Nice to meet you Alice!", 24, 7)
    client.post(
        "/chat",
        json={"session_id": "multi-sess-1", "message": "What is my name?"},
    )

    # Verify history via GET /sessions/{session_id}/messages
    history_res = client.get("/sessions/multi-sess-1/messages")
    assert history_res.status_code == 200
    data = history_res.json()
    assert data["session_id"] == "multi-sess-1"
    messages = data["messages"]
    assert len(messages) == 4
    # Oldest first: user, assistant, user, assistant
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hi, I am Alice"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hello! How can I help?"
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "What is my name?"
    assert messages[3]["role"] == "assistant"
    assert messages[3]["content"] == "Nice to meet you Alice!"

    # Verify unknown session returns 404 {"detail": "session not found"}
    unknown_res = client.get("/sessions/nonexistent-session-xyz/messages")
    assert unknown_res.status_code == 404
    assert unknown_res.json() == {"detail": "session not found"}


def test_sqlite_persistence_across_connections():
    from app.database import get_connection, save_turn, get_messages_for_session
    # Write turn with connection 1
    session_id = "persistence-test-sess"
    save_turn(
        session_id=session_id,
        user_content="Hello SQLite",
        assistant_content="Stored safely",
        metadata={"resolution_source": "LIVE_INFERENCE"},
    )

    # Read back with a separate connection
    messages = get_messages_for_session(session_id)
    assert len(messages) == 2
    assert messages[0]["content"] == "Hello SQLite"
    assert messages[1]["content"] == "Stored safely"
    assert messages[1]["metadata"]["resolution_source"] == "LIVE_INFERENCE"
