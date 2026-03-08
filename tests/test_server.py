import time

from fastapi.testclient import TestClient

from new_app import server as server_module


def test_logs_endpoint_exposes_entries() -> None:
    with TestClient(server_module.app) as client:
        response = client.get("/logs")
        assert response.status_code == 200
        body = response.json()
        assert "logs" in body
        assert isinstance(body["logs"], list)


def test_history_endpoint_returns_game_states() -> None:
    with TestClient(server_module.app) as client:
        time.sleep(0.6)
        response = client.get("/history")
        assert response.status_code == 200
        body = response.json()
        assert "history" in body
        history = body["history"]
        assert isinstance(history, list)
        assert history
        first = history[0]
        assert "beat" in first
        assert "state" in first
        assert isinstance(first["state"], dict)


def test_websocket_receives_state_updates() -> None:
    with TestClient(server_module.app) as client:
        with client.websocket_connect("/ws/game-state") as websocket:
            time.sleep(0.8)
            message = websocket.receive_json()
            assert isinstance(message, dict)
            assert "state" in message
            assert "current_beat" in message["state"]
