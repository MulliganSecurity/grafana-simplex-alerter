import pytest
import tempfile
import os
from simplex_alerter.config import load_config, get_config


def test_load_valid_config():
    config_content = """
alert_groups:
  - endpoint_name: mygroup
    invite_link: "https://simplex.chat/contact#/..."
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        tmpfile = f.name
    try:
        load_config(tmpfile)
        config = get_config()
        assert "alert_groups" in config
        assert config["alert_groups"][0]["endpoint_name"] == "mygroup"
    finally:
        os.unlink(tmpfile)


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.yml")


def test_bot_name_optional():
    config_content = """
alert_groups:
  - endpoint_name: mygroup
    invite_link: "https://simplex.chat/contact#/..."
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        tmpfile = f.name
    try:
        load_config(tmpfile)
        config = get_config()
        assert config.get("bot_name") is None
    finally:
        os.unlink(tmpfile)


def test_bot_name_present():
    config_content = """
bot_name: alertBot
alert_groups:
  - endpoint_name: mygroup
    invite_link: "https://simplex.chat/contact#/..."
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write(config_content)
        tmpfile = f.name
    try:
        load_config(tmpfile)
        config = get_config()
        assert config.get("bot_name") == "alertBot"
    finally:
        os.unlink(tmpfile)
