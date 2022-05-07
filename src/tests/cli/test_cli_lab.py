# -*- coding: utf-8 -*-
import re

import pytest
import yaml
from click.testing import CliRunner, Result

from evengsdk.cli.cli import main as cli


@pytest.fixture
def topology_file(datadir, authenticated_client, helpers):
    """Load and return the topology file"""
    if authenticated_client.api.is_community:
        topo_file = datadir / "topology_community.yml"
    else:
        topo_file = datadir / "topology_pro.yml"

    topo_data = yaml.safe_load(topo_file.read_text())
    new_name = f"test-lab-{helpers.get_timestamp()}"
    topo_data["name"] = new_name
    lab_path = topo_data["path"] + new_name

    topo_file.write_text(yaml.dump(topo_data))

    yield topo_file
    helpers.run_cli_command(["lab", "delete", "--path", lab_path])


@pytest.fixture
def topology_tempdir(datadir):
    """Return template directory"""
    return datadir / "templates"


@pytest.mark.usefixtures("test_cli_lab")
class TestLabCommands:
    """CLI Lab Commands"""

    def test_lab_single_edit(self, helpers, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'edit' subcommand.
        Assert: The output indicates that lab is updated successfully.
        """
        result = helpers.run_cli_command(
            ["lab", "edit", "--version", "2", "--path", cli_lab_path]
        )
        assert result.exit_code == 0, result.output
        assert "success" in result.output.lower()

    def test_lab_edit_multiple_fields_fails(self, helpers, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'edit' subcommand.
        Assert: That only a single field can be set a time.
        """
        result = helpers.run_cli_command(
            [
                "lab",
                "edit",
                "--version",
                "3",
                "--author",
                "tester",
                "--path",
                cli_lab_path,
            ]
        )
        assert result.exit_code > 0, result.output
        assert "may only set one at a time" in result.output.lower()

    def test_lab_read(self, cli_lab, helpers, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'read' subcommand.
        Assert: The output indicates that lab is retrieved successfully.
        """
        result = helpers.run_cli_command(["lab", "read", "--path", cli_lab_path])
        assert result.exit_code == 0, result.output
        assert cli_lab["name"] in result.output

    @pytest.mark.parametrize("subcommand", ["read", "edit", "delete", "start", "stop"])
    def test_lab_update_non_existent(self, helpers, subcommand):
        """
        Arrange/Act: Run the `lab` command with crud subcommands for a non-existant lab.
        Assert: The output indicates that lab is errors are correctly displayed without traceback.
        """
        result = helpers.run_cli_command(["lab", subcommand, "--path", "/n0n-e0xist"])
        assert result.exit_code > 0, result.output
        assert "does not exist" in result.output.lower()

    @pytest.mark.parametrize(
        "subcommand,option", [("import", "--src"), ("export", "--path")]
    )
    def test_lab_import_export_nonexistent(self, helpers, subcommand, option):
        """
        Arrange/Act: Run the `lab` command with the 'import' subcommand.
        Assert: The output indicates that lab topology subcommand produces an error and does not crash.
        """
        result = helpers.run_cli_command(["lab", subcommand, option, "/n0n-existent"])
        assert result.exit_code > 0
        assert (
            "does not exist" in result.output.lower()
            or "Cannot export lab" in result.output
        )

    def test_lab_start(self, helpers, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'start' subcommand.
        Assert: The output indicates that lab is started successfully.
        """
        result = helpers.run_cli_command(["lab", "start", "--path", cli_lab_path])
        assert result.exit_code == 0, result.output

    def test_lab_stop(self, helpers, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'stop' subcommand.
        Assert: The output indicates that lab is stopped successfully.
        """
        result = helpers.run_cli_command(["lab", "stop", "--path", cli_lab_path])
        assert result.exit_code == 0, result.output

    def test_lab_list(self, helpers, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'list' subcommand.
        Assert: The output indicates that labs are listed successfully.
        """
        result = helpers.run_cli_command(["lab", "list"])
        assert result.exit_code == 0, result.output
        assert cli_lab_path in result.output

    def test_list_lab_topology_error(self, helpers, test_node):
        """
        Arrange/Act: Run the `lab` command with the 'topology' subcommand for a non-existing lab.
        Assert: The output indicates that lab topology subcommand produces an error and does not crash.
        """
        result = helpers.run_cli_command(["lab", "topology", "--path", "/n0n-existent"])
        assert result.exit_code > 0
        assert "does not exist" in result.output.lower()

    def test_list_lab_topology_empty(self, helpers, cli_lab_path):
        """
        Arrange/Act: Run the `lab` command with the 'topology' for an empty lab.
        Assert: The output indicates that lab topology subcommand produces an error and does not crash.
        """
        result = helpers.run_cli_command(["lab", "topology", "--path", cli_lab_path])
        assert result.exit_code > 0
        assert "lab empty?" in result.output.lower()

    def test_lab_topology_builder(self, helpers, topology_file, topology_tempdir):
        """
        Arrange/Act: Run the `lab` command with the 'topology' subcommand.
        Assert: The output indicates that lab topology subcommand produces an error and does not crash.
        """
        result = helpers.run_cli_command(
            [
                "lab",
                "create-from-topology",
                "-t",
                str(topology_file),
                "--template-dir",
                topology_tempdir,
            ]
        )
        assert result.exit_code == 0, result.output

    def test_lab_topology_builder_bad_param(self, helpers):
        """
        Arrange/Act: Run the `lab` command with the 'topology' subcommand.
        Assert: The output indicates that lab topology subcommand produces an error and does not crash.
        """
        result = helpers.run_cli_command(
            ["lab", "create-from-topology", "-t", "non-existent-file"]
        )
        assert "Path 'non-existent-file' does not exist" in result.output

    def test_lab_topology_builder_already_exists(
        self, helpers, topology_file, topology_tempdir, cli_lab
    ):
        """
        Arrange/Act: Run the `lab` command with the 'topology' subcommand.
        Assert: The output indicates that lab topology subcommand produces an error and does not crash.
        """
        topo_data = yaml.safe_load(topology_file.read_text())
        topo_data["name"] = cli_lab["name"]
        topology_file.write_text(yaml.dump(topo_data))

        result = helpers.run_cli_command(
            [
                "lab",
                "create-from-topology",
                "-t",
                str(topology_file),
                "--template-dir",
                topology_tempdir,
            ]
        )
        assert "already exists" in result.output

    def test_lab_import_fails_with_error_message(
        self, helpers, datadir, escape_ansi_regex
    ):
        """
        Arrange/Act: Run the `lab` command with the 'import' subcommand.
        Assert: The output indicates that lab topology subcommand produces an error and does not crash.
        """
        src_dir = datadir / "test.zip"
        result = helpers.run_cli_command(["lab", "import", "--src", src_dir])
        assert result.exit_code > 0

        escaped_result = escape_ansi_regex.sub("", result.output)
        assert "ERROR:" in escaped_result

    def test_lab_create_fails_with_error_message(
        self, helpers, cli_lab_path, escape_ansi_regex
    ):
        """
        Arrange/Act: Run the `lab` command with the 'create' subcommand.
        Assert: The output indicates that lab create subcommand produces an error and does not crash.
        """
        result = helpers.run_cli_command(
            [
                "lab",
                "create",
                "--path",
                cli_lab_path,
                "--name",
                "test",
                "--version",
                "-999999999",
            ]
        )
        assert result.exit_code > 0

        escaped_result = escape_ansi_regex.sub("", result.output)
        assert "ERROR:" in escaped_result


@pytest.mark.usefixtures("test_cli_lab")
class TestImportExportCommands:
    """Test Import/Export Commands"""

    def test_lab_export_and_import(
        self, cli_lab_path, authenticated_client, escape_ansi_regex
    ):
        """
        Arrange/Act: Run the `lab` command with the 'export' subcommand.
        Assert: The output indicates that lab exported successfully.
        """
        path = f"{cli_lab_path}.unl"
        runner: CliRunner = CliRunner(env={"EVE_NG_LAB_PATH": path})
        with runner.isolated_filesystem():
            # Export the lab
            result: Result = runner.invoke(cli, ["lab", "export", "--path", path])
            assert result.exit_code == 0, result.output
            assert "Lab exported" in result.output
            result = escape_ansi_regex.sub("", result.output)

            # grab the exported lab
            if authenticated_client.api.is_community:
                match = re.search(r"unetlab_.*zip", result)
            else:
                match = re.search(r"eve-ng_.*zip", result)
            zipname = match[0]

            # Import the lab
            result2: Result = runner.invoke(cli, ["lab", "import", "--src", zipname])
            assert result2.exit_code == 0, result2.output
            assert "imported" in result2.output
