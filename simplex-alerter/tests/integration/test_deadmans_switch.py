"""Integration tests for the dead man's switch notifier and monitor_channels."""
import asyncio
import pytest
import time_machine
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from simplex_alerter.chat import deadmans_switch_notifier, monitor_channels


def _make_liveness(
    *,
    alert_threshold_seconds=3600,
    trigger_threshold_seconds=7200,
    alert_sent=False,
    switch_triggered=False,
    last_seen=None,
):
    return {
        "testuser": {
            "group": "testgroup",
            "alert_threshold_seconds": timedelta(seconds=alert_threshold_seconds),
            "trigger_threshold_seconds": timedelta(seconds=trigger_threshold_seconds),
            "alert_message": "User has been inactive",
            "inheritance_filepath": "/tmp/inheritance.txt",
            "inheritance_message": "Here is the document",
            "last_seen": last_seen or datetime.now(),
            "alert_sent": alert_sent,
            "switch_triggered": switch_triggered,
        }
    }


@pytest.fixture
def mock_client():
    client = AsyncMock()
    client.api_get_groups = AsyncMock(
        return_value={"type": "groupsList", "groups": [
            [{"groupProfile": {"displayName": "testgroup"}, "groupId": 99}]
        ]}
    )
    client.api_send_text_message = AsyncMock(return_value=[])
    client.api_send_file = AsyncMock(return_value=[])
    client.msg_q = AsyncMock()
    return client


async def _run_one_tick(coro):
    """Run a coroutine that loops forever, cancelling after one iteration."""
    task = asyncio.create_task(coro)
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


async def test_alert_fires_after_alert_threshold(mock_client):
    """alert_message is sent once the alert_threshold_seconds window passes."""
    past = datetime.now() - timedelta(seconds=3601)
    liveness = _make_liveness(alert_threshold_seconds=3600, last_seen=past)

    with patch("simplex_alerter.chat.get_groups", new=AsyncMock(return_value={"testgroup": 99})), \
         patch("asyncio.sleep", new=AsyncMock()):
        await _run_one_tick(deadmans_switch_notifier(liveness, mock_client))

    mock_client.api_send_text_message.assert_called_once()
    assert liveness["testuser"]["alert_sent"] is True


async def test_alert_not_fired_before_threshold(mock_client):
    """No alert is sent when last_seen is recent."""
    liveness = _make_liveness(alert_threshold_seconds=3600)  # last_seen = now

    with patch("simplex_alerter.chat.get_groups", new=AsyncMock(return_value={"testgroup": 99})), \
         patch("asyncio.sleep", new=AsyncMock()):
        await _run_one_tick(deadmans_switch_notifier(liveness, mock_client))

    mock_client.api_send_text_message.assert_not_called()
    assert liveness["testuser"]["alert_sent"] is False


async def test_inheritance_file_sent_after_trigger_threshold(mock_client):
    """File is uploaded after trigger_threshold_seconds."""
    past = datetime.now() - timedelta(seconds=7201)
    liveness = _make_liveness(
        alert_threshold_seconds=3600,
        trigger_threshold_seconds=7200,
        alert_sent=True,  # alert already sent
        last_seen=past,
    )

    with patch("simplex_alerter.chat.get_groups", new=AsyncMock(return_value={"testgroup": 99})), \
         patch("asyncio.sleep", new=AsyncMock()):
        await _run_one_tick(deadmans_switch_notifier(liveness, mock_client))

    mock_client.api_send_file.assert_called_once()
    assert liveness["testuser"]["switch_triggered"] is True


async def test_alert_sent_flag_prevents_duplicate_alerts(mock_client):
    """With alert_sent=True, no additional text message is sent."""
    past = datetime.now() - timedelta(seconds=3601)
    liveness = _make_liveness(alert_threshold_seconds=3600, alert_sent=True, last_seen=past)

    with patch("simplex_alerter.chat.get_groups", new=AsyncMock(return_value={"testgroup": 99})), \
         patch("asyncio.sleep", new=AsyncMock()):
        await _run_one_tick(deadmans_switch_notifier(liveness, mock_client))

    mock_client.api_send_text_message.assert_not_called()


async def test_switch_triggered_flag_prevents_duplicate_file_sends(mock_client):
    """With switch_triggered=True, the file is not uploaded a second time."""
    past = datetime.now() - timedelta(seconds=7201)
    liveness = _make_liveness(
        trigger_threshold_seconds=7200,
        alert_sent=True,
        switch_triggered=True,
        last_seen=past,
    )

    with patch("simplex_alerter.chat.get_groups", new=AsyncMock(return_value={"testgroup": 99})), \
         patch("asyncio.sleep", new=AsyncMock()):
        await _run_one_tick(deadmans_switch_notifier(liveness, mock_client))

    mock_client.api_send_file.assert_not_called()


async def test_monitor_channels_resets_timer_on_activity(mock_client):
    """monitor_channels updates last_seen and resets alert_sent when a message is seen."""
    old_time = datetime.now() - timedelta(seconds=5000)
    liveness = _make_liveness(alert_sent=True, last_seen=old_time)

    incoming_msg = {
        "type": "newChatItems",
        "chatItems": [
            {
                "chatInfo": {
                    "groupInfo": {
                        "groupProfile": {"displayName": "testgroup"}
                    }
                },
                "chatItem": {
                    "chatDir": {
                        "groupMember": {
                            "memberProfile": {"displayName": "testuser"}
                        }
                    }
                },
            }
        ],
    }

    # msg_q.dequeue returns the message once, then hangs (CancelledError on next call)
    call_count = 0

    async def fake_dequeue():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return incoming_msg
        # Block until cancelled
        await asyncio.sleep(9999)

    mock_client.msg_q.dequeue = fake_dequeue

    with patch("aiofiles.open"), \
         patch("simplex_alerter.chat.pickle") as mock_pickle:
        mock_pickle.dumps = MagicMock(return_value=b"pickled")
        # Need aiofiles to work as async context manager
        import aiofiles
        mock_file = AsyncMock()
        mock_file.__aenter__ = AsyncMock(return_value=mock_file)
        mock_file.__aexit__ = AsyncMock(return_value=False)
        mock_file.write = AsyncMock()
        with patch("aiofiles.open", return_value=mock_file):
            await _run_one_tick(monitor_channels(liveness, {"groups": {}, "users": {}}, mock_client))

    assert liveness["testuser"]["alert_sent"] is False
    assert liveness["testuser"]["last_seen"] > old_time
