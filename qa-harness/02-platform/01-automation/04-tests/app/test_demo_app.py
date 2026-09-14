import os

import pytest


@pytest.mark.app
@pytest.mark.skipif(os.getenv("TA_RUN_APP") != "1", reason="Set TA_RUN_APP=1 to enable app tests")
def test_app_demo_placeholder():
    # Placeholder: enable and implement when Appium server + device is ready.
    assert True
