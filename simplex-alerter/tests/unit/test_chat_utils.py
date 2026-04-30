import pytest
from unittest.mock import AsyncMock, patch
from simplex_alerter.chat import get_groups


async def test_get_groups_populated():
    group_data = {
        "groups": [
            [{"groupProfile": {"displayName": "alerts"}, "groupId": 1}],
            [{"groupProfile": {"displayName": "monitoring"}, "groupId": 2}],
        ]
    }
    with patch("simplex_alerter.chat.traced", lambda **kw: lambda f: f):
        result = await get_groups(group_data)
    assert result == {"alerts": 1, "monitoring": 2}


async def test_get_groups_empty():
    group_data = {"groups": []}
    with patch("simplex_alerter.chat.traced", lambda **kw: lambda f: f):
        result = await get_groups(group_data)
    assert result == {}


async def test_get_groups_skips_malformed():
    group_data = {
        "groups": [
            [{"groupProfile": {"displayName": "good"}, "groupId": 10}],
            [{"noGroupProfile": True}],
        ]
    }
    with patch("simplex_alerter.chat.traced", lambda **kw: lambda f: f):
        result = await get_groups(group_data)
    assert "good" in result
    assert len(result) == 1
