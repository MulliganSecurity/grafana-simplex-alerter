import pytest
from simplex_alerter.webhook.request_models.grafana import GrafanaAlert


async def test_grafana_render_title(sample_grafana_payload):
    model = GrafanaAlert(**sample_grafana_payload)
    result = await model.render()
    assert "CPU Usage High" in result


async def test_grafana_render_message(sample_grafana_payload):
    model = GrafanaAlert(**sample_grafana_payload)
    result = await model.render()
    assert "CPU usage has exceeded 90% for 5 minutes" in result


async def test_grafana_render_firing():
    model = GrafanaAlert(
        title="[FIRING] Alert",
        message="Something is on fire",
    )
    result = await model.render()
    assert "[FIRING] Alert" in result
    assert "Something is on fire" in result


async def test_grafana_render_resolved():
    model = GrafanaAlert(
        title="[RESOLVED] Alert",
        message="Everything is fine now",
    )
    result = await model.render()
    assert "[RESOLVED] Alert" in result
    assert "Everything is fine now" in result


async def test_grafana_render_format(sample_grafana_payload):
    model = GrafanaAlert(**sample_grafana_payload)
    result = await model.render()
    assert result == "CPU Usage High\nCPU usage has exceeded 90% for 5 minutes"
