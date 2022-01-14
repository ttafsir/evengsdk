from pathlib import Path

import yaml

from evengsdk.schemas.validator import SchemaValidator
from evengsdk.templates import ConfigTemplateBuilder


class Topology:
    def __init__(self, data_dict: dict):
        self.validator = SchemaValidator()
        self.instance = data_dict
        self.config_builder = ConfigTemplateBuilder()
        self._lab = None
        self._path = None
        self._configurations = {}

    def validate(self):
        return self.validator.validate(self.instance)

    def _get_lab(self):
        return {
            "name": self.instance.get("name"),
            "description": self.instance.get("description"),
            "version": self.instance.get("version"),
            "path": self.instance.get("path"),
            "body": self.instance.get("body"),
            "author": self.instance.get("author"),
        }

    @property
    def lab(self):
        return self._get_lab()

    def _get_path(self):
        return f'{self.lab["path"]}/{self.lab["name"]}.unl'

    @property
    def path(self):
        return self._get_path()

    @property
    def nodes(self):
        return self.instance.get("nodes")

    @property
    def networks(self):
        return self.instance.get("networks")

    @property
    def cloud_links(self):
        return self.instance.get("links", {}).get("network")

    @property
    def p2p_links(self):
        return self.instance.get("links", {}).get("node")

    def _load_file_content(self, config_path: Path) -> str:
        """Load device config"""
        return config_path.read_text()

    def render_node_config(self, template: str, data: dict) -> str:
        """Render node config"""
        return self.config_builder.render_template(template, data)

    def build_node_configs(self, template_dir: str = "templates"):
        """Build node configs"""
        for node in self.nodes:
            node_name = node["name"]

            if not node.get("configuration"):
                continue

            # configuration key is only needed for config builds, not for the API
            config_options = node.pop("configuration")

            if "file" in config_options:
                config_path = Path(config_options["file"])
                if not config_path.exists():
                    raise FileNotFoundError(f"Config file {config_path} not found")
                self._configurations[node_name] = self._load_file_content(config_path)

            if "template" in config_options:
                context_data = config_options.get("vars") or config_options.get(
                    "vars_file"
                )
                if isinstance(context_data, str):
                    context_data = yaml.safe_load(
                        self._load_file_content(Path(context_data))
                    )
                if template_dir:
                    self.config_builder.template_path = Path(template_dir)

                self._configurations[node_name] = self.render_node_config(
                    config_options["template"], context_data
                )

    def get_node_config(self, node_name: str):
        """Get node config"""
        return self._configurations.get(node_name)
