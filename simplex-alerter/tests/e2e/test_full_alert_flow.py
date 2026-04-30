import os
import pytest
import httpx


@pytest.mark.e2e
def test_grafana_alert_returns_200():
    """POST a minimal Grafana alert to the running alerter and assert HTTP 200."""
    endpoint = os.environ["SIMPLEX_TEST_ENDPOINT"]
    payload = {
        "receiver": "test",
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "TestAlert", "severity": "critical"},
                "annotations": {"summary": "E2E test alert"},
                "startsAt": "2024-01-01T00:00:00Z",
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "",
                "fingerprint": "abc123",
            }
        ],
        "groupLabels": {},
        "commonLabels": {"alertname": "TestAlert"},
        "commonAnnotations": {},
        "externalURL": "",
        "version": "4",
        "groupKey": "{}:{}",
        "truncatedAlerts": 0,
        "title": "[FIRING:1] TestAlert",
        "state": "alerting",
        "message": "E2E test alert",
    }
    response = httpx.post(f"{endpoint}/test", json=payload)
    assert response.status_code == 200
