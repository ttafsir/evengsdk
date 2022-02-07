from datetime import datetime
import os

import pytest
from dotenv import load_dotenv


load_dotenv()


@pytest.fixture(scope="module")
def setup_cli_lab(cli_lab, authenticated_client):
    lab_obj = authenticated_client.api.create_lab(**cli_lab)
    yield lab_obj
    authenticated_client.login(
        username=os.environ["EVE_NG_USERNAME"], password=os.environ["EVE_NG_PASSWORD"]
    )
    authenticated_client.api.delete_lab(cli_lab["path"] + cli_lab["name"])


@pytest.fixture(scope="module")
def cli_lab():
    now = datetime.now()
    ts = str(datetime.timestamp(now)).split(".")[0]
    return {"name": f"test-cli-lab-{ts}", "description": "Test Lab", "path": "/"}


@pytest.fixture()
def cli_lab_path(cli_lab):
    return cli_lab["path"] + cli_lab["name"]
