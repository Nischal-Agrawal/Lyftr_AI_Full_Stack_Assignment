import pytest


def test_validation_empty_message(client):
    response = client.post("/chat", json={"session_id": "test-session", "message": ""})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_validation_whitespace_only_message(client):
    response = client.post("/chat", json={"session_id": "test-session", "message": "     "})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_validation_message_exceeding_4000_chars(client):
    long_msg = "x" * 4001
    response = client.post("/chat", json={"session_id": "test-session", "message": long_msg})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_validation_empty_session_id(client):
    response = client.post("/chat", json={"session_id": "", "message": "hello"})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_validation_session_id_too_long(client):
    long_session = "s" * 129
    response = client.post("/chat", json={"session_id": long_session, "message": "hello"})
    assert response.status_code == 422
    assert "detail" in response.json()


def test_validation_malformed_json(client):
    response = client.post(
        "/chat",
        content="This is not JSON",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert "detail" in response.json()
