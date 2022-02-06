from datetime import datetime

import pytest


@pytest.fixture(scope="module")
def setup_lab(lab, authenticated_client):
    lab_obj = authenticated_client.api.create_lab(**lab)
    yield lab_obj
    authenticated_client.api.delete_lab(lab["path"] + lab["name"])


@pytest.fixture(scope="module")
def lab():
    now = datetime.now()
    ts = str(datetime.timestamp(now)).split(".")[0]
    return {"name": f"test-lab-{ts}", "description": "Test Lab", "path": "/"}


@pytest.fixture()
def lab_path(lab):
    return lab["path"] + lab["name"]
