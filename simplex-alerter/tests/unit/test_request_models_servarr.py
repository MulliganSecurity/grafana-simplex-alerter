import pytest
from simplex_alerter.webhook.request_models.servarr import SonarrAlert


async def test_sonarr_render_series_title(sample_sonarr_payload):
    model = SonarrAlert(**sample_sonarr_payload)
    result = await model.render()
    assert "Breaking Bad" in result


async def test_sonarr_render_event_type(sample_sonarr_payload):
    model = SonarrAlert(**sample_sonarr_payload)
    result = await model.render()
    assert "Download" in result


async def test_sonarr_render_episode(sample_sonarr_payload):
    model = SonarrAlert(**sample_sonarr_payload)
    result = await model.render()
    assert "S1E1" in result or "S01E01" in result


async def test_sonarr_render_release_title(sample_sonarr_payload):
    model = SonarrAlert(**sample_sonarr_payload)
    result = await model.render()
    assert "Breaking.Bad.S01E01" in result


async def test_sonarr_render_indexer(sample_sonarr_payload):
    model = SonarrAlert(**sample_sonarr_payload)
    result = await model.render()
    assert "NZBGeek" in result


async def test_sonarr_minimal_payload():
    model = SonarrAlert(eventType="Test")
    result = await model.render()
    assert "Test" in result


async def test_sonarr_movie_payload():
    model = SonarrAlert(
        eventType="Download",
        movie={
            "title": "Inception",
            "overview": "A mind-bending thriller",
        },
    )
    result = await model.render()
    assert "Inception" in result
    assert "A mind-bending thriller" in result
