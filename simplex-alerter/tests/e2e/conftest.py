import os
import pytest


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end (requires live alerter endpoint)"
    )


def pytest_collection_modifyitems(config, items):
    endpoint = os.environ.get("SIMPLEX_TEST_ENDPOINT")
    if not endpoint:
        skip_e2e = pytest.mark.skip(
            reason="SIMPLEX_TEST_ENDPOINT not set; skipping E2E tests"
        )
        for item in items:
            if item.get_closest_marker("e2e"):
                item.add_marker(skip_e2e)
