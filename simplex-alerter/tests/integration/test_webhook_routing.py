"""Integration tests for webhook routing."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

import simplex_alerter.webhook as webhook_module
from simplex_alerter.webhook import app


@pytest.fixture(autouse=True)
def reset_webhook_globals():
    """Reset module-level globals between tests."""
    original_map = webhook_module.endpoint_group_map.copy()
    original_endpoint = webhook_module.simplex_endpoint
    original_db = webhook_module.db_path
    yield
    webhook_module.endpoint_group_map.clear()
    webhook_module.endpoint_group_map.update(original_map)
    webhook_module.simplex_endpoint = original_endpoint
    webhook_module.db_path = original_db


@pytest.fixture
def mock_chat_client():
    client = AsyncMock()
    client.connected = True
    client.api_get_groups = AsyncMock(
        return_value={
            "type": "groupsList",
            "groups": [
                [{"groupProfile": {"displayName": "mygroup"}, "groupId": 42}]
            ],
        }
    )
    client.api_send_text_message = AsyncMock(return_value=[])
    return client


@pytest.fixture
def test_client(mock_chat_client):
    """Build a TestClient with lifespan bypassed via app.state injection."""
    webhook_module.simplex_endpoint = "ws://localhost:7897"
    webhook_module.db_path = "/tmp/test-db"

    with patch("simplex_alerter.webhook.subprocess.Popen"), \
         patch("simplex_alerter.webhook.ChatClient.create", return_value=mock_chat_client), \
         patch("simplex_alerter.webhook.load_liveness_data", new=AsyncMock()), \
         patch("simplex_alerter.webhook.monitor_channels", new=AsyncMock()), \
         patch("simplex_alerter.webhook.deadmans_switch_notifier", new=AsyncMock()), \
         patch("simplex_alerter.webhook.get_config", return_value={"alert_groups": []}), \
         patch("simplex_alerter.webhook.get_groups", new=AsyncMock(return_value={"mygroup": 42})):
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c, mock_chat_client


def test_post_to_known_group_returns_200(test_client):
    client, mock_chat = test_client
    with patch("simplex_alerter.webhook.get_groups", new=AsyncMock(return_value={"mygroup": 42})):
        response = client.post(
            "/mygroup",
            json={"title": "Test Alert", "message": "Something broke"},
        )
    assert response.status_code == 200


def test_post_to_unknown_group_returns_404(test_client):
    client, mock_chat = test_client
    with patch("simplex_alerter.webhook.get_groups", new=AsyncMock(return_value={"mygroup": 42})):
        response = client.post(
            "/nonexistent_group",
            json={"title": "Test Alert", "message": "Something broke"},
        )
    assert response.status_code == 404


def test_post_unknown_model_falls_back_to_raw_json(test_client):
    """An unrecognised payload (not matching any KnownModels) is forwarded as raw JSON."""
    client, mock_chat = test_client
    with patch("simplex_alerter.webhook.get_groups", new=AsyncMock(return_value={"mygroup": 42})):
        response = client.post(
            "/mygroup",
            json={"totally": "unknown", "payload": True, "nested": {"x": 1}},
        )
    assert response.status_code == 200


def test_get_metrics_returns_200(test_client):
    client, _ = test_client
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_wrong_bearer_token_returns_401(test_client):
    """When webhook_secret is set, a wrong token returns 401."""
    client, mock_chat = test_client
    with patch("simplex_alerter.webhook.get_config", return_value={"alert_groups": [], "webhook_secret": "correct-secret"}), \
         patch("simplex_alerter.webhook.get_groups", new=AsyncMock(return_value={"mygroup": 42})):
        response = client.post(
            "/mygroup",
            json={"title": "Test Alert", "message": "Something broke"},
            headers={"Authorization": "Bearer wrong-token"},
        )
    assert response.status_code == 401


def test_correct_bearer_token_succeeds(test_client):
    """When webhook_secret is set, the correct token allows the request through."""
    client, mock_chat = test_client
    with patch("simplex_alerter.webhook.get_config", return_value={"alert_groups": [], "webhook_secret": "correct-secret"}), \
         patch("simplex_alerter.webhook.get_groups", new=AsyncMock(return_value={"mygroup": 42})):
        response = client.post(
            "/mygroup",
            json={"title": "Test Alert", "message": "Something broke"},
            headers={"Authorization": "Bearer correct-secret"},
        )
    assert response.status_code == 200
