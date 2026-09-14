import os

import pytest


@pytest.mark.web
@pytest.mark.skipif(os.getenv("TA_RUN_WEB") != "1", reason="Set TA_RUN_WEB=1 to enable web UI tests")
def test_web_demo_placeholder():
    # Placeholder: project BDD web tests live in the project's features/ tree.
    assert True
