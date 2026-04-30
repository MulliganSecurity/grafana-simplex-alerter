import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_chat_client():
    client = AsyncMock()
    client.send_message = AsyncMock()
    client.get_groups = AsyncMock()
    return client


@pytest.fixture
def sample_sonarr_payload():
    return {
        "eventType": "Download",
        "series": {
            "title": "Breaking Bad",
            "year": 2008,
            "tvdbId": 81189,
        },
        "episodes": [
            {"seasonNumber": 1, "episodeNumber": 1, "title": "Pilot"},
        ],
        "release": {
            "releaseTitle": "Breaking.Bad.S01E01",
            "indexer": "NZBGeek",
        },
    }


@pytest.fixture
def sample_grafana_payload():
    return {
        "title": "CPU Usage High",
        "message": "CPU usage has exceeded 90% for 5 minutes",
    }


@pytest.fixture
def sample_forgejo_push_payload():
    return {
        "ref": "refs/heads/main",
        "before": "abc123",
        "after": "def456",
        "compare_url": "https://forgejo.example.com/repo/compare",
        "commits": [
            {
                "id": "def456",
                "message": "Add new feature",
                "author": {"name": "Alice"},
            }
        ],
        "total_commits": 1,
        "head_commit": {
            "id": "def456",
            "message": "Add new feature",
            "author": {"name": "Alice"},
        },
        "repository": {
            "full_name": "alice/my-repo",
        },
        "pusher": {"login": "alice"},
        "sender": {"login": "alice"},
    }
