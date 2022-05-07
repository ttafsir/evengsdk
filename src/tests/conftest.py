import os
import re
from datetime import datetime
from distutils import dir_util
from pathlib import Path

import pytest
from click.testing import CliRunner, Result
from dotenv import load_dotenv

from evengsdk.cli.cli import main as cli
from evengsdk.client import EvengClient

load_dotenv()


class Helpers:
    """Helper functions for CLI tests."""

    @staticmethod
    def run_cli_command(commands: list) -> Result:
        """Helper function to Run CLI command."""
        runner: CliRunner = CliRunner()
        return runner.invoke(cli, commands)

    @staticmethod
    def get_timestamp() -> str:
        """Get timestamp."""
        now = datetime.now()
        return str(datetime.timestamp(now)).split(".", maxsplit=1)[0]


@pytest.fixture(scope="session")
def helpers():
    """returns a Helpers object as a fixture."""
    return Helpers


@pytest.fixture(scope="session")
def escape_ansi_regex():
    """Escape ANSI chars from CLI output"""
    # replace ansi escape sequences
    # https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python
    return re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


@pytest.fixture(scope="session")
def client():
    """Create and teardown client"""
    client = EvengClient(
        os.environ["EVE_NG_HOST"], log_file="test.log", log_level="DEBUG"
    )
    if os.environ["EVE_NG_PROTOCOL"] == "https":
        client.protocol = "https"
        client.ssl_verify = False
        client.disable_insecure_warnings = True
    return client


@pytest.fixture(scope="module")
def authenticated_client(client):
    """Authenticate client and return client object."""
    username = os.environ["EVE_NG_USERNAME"]
    passwd = os.environ["EVE_NG_PASSWORD"]
    client.login(username=username, password=passwd)
    yield client
    client.logout()


@pytest.fixture(scope="session")
def lab(helpers):
    """Create lab fixture."""
    return {
        "name": f"test-lab-{helpers.get_timestamp()}",
        "description": "Test Lab",
        "path": "/",
    }


@pytest.fixture(scope="module")
def cli_lab(helpers):
    """Create lab fixture."""
    return {
        "name": f"test-cli-lab-{helpers.get_timestamp()}",
        "description": "Test Lab",
        "path": "/",
    }


@pytest.fixture()
def lab_path(lab):
    """Return lab path for API tests"""
    return lab["path"] + lab["name"]


@pytest.fixture(scope="module")
def cli_lab_path(cli_lab):
    """Return lab path for CLI tests"""
    return cli_lab["path"] + cli_lab["name"]


@pytest.fixture()
def network_name():
    return "vCloud"


@pytest.fixture()
def test_network_data():
    """returns a dict with test data for a network"""
    return dict(name="test_network", network_type="bridge")


@pytest.fixture(scope="session")
def test_user_data():
    """Test user data."""
    return {
        "username": "testuser99",
        "password": "password1",
        "expiration": "-1",
        "role": "admin",
        "name": "John Doe",
        "email": "john.doe@acme.com",
    }


@pytest.fixture(scope="session")
def test_node_data():
    """returns a dict with test data for a node"""
    return {
        "node_type": "qemu",
        "template": "veos",
        "image": "veos-4.21.1.1F",
        "name": "leaf01",
        "ethernet": 4,
        "cpu": 2,
        "serial": 2,
        "delay": 0,
    }


@pytest.fixture(scope="session")
def test_node_config():
    """Test config data for a node."""
    return """
!
hostname vEOS4
!
"""


@pytest.fixture(scope="module")
def test_cli_lab(cli_lab, cli_lab_path, helpers):
    """Create Test user."""
    cli_args = [
        "--name",
        cli_lab["name"],
        "--description",
        cli_lab["description"],
        "--path",
        cli_lab["path"],
    ]
    yield helpers.run_cli_command(["lab", "create", *cli_args])
    helpers.run_cli_command(["lab", "delete", "--path", cli_lab_path])


@pytest.fixture(scope="module")
def test_node(test_node_data, cli_lab, cli_lab_path, helpers):
    """Create Test user."""
    cli_commands = [
        "node",
        "create",
        "--path",
        cli_lab_path,
        "--node-type",
        test_node_data["node_type"],
        "--name",
        test_node_data["name"],
        "--template",
        test_node_data["template"],
        "--ethernet",
        test_node_data["ethernet"],
    ]
    yield helpers.run_cli_command(cli_commands)
    helpers.run_cli_command(["node", "delete", "-n", "1", "--path", cli_lab_path])


@pytest.fixture(scope="module")
def datadir(tmp_path_factory, request):
    """
    Search a folder with the same name of test module and, if available,
    copy all contents to a temporary directory for test data.
    """
    filename = request.module.__file__
    test_dir = Path(filename).parent / Path(filename).stem
    temp_path = tmp_path_factory.mktemp(test_dir.stem)

    if os.path.isdir(test_dir):
        dir_util.copy_tree(test_dir, str(temp_path))

    return temp_path
