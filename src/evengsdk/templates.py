from pathlib import Path
from typing import Union, List, Any

from jinja2 import Environment, FileSystemLoader, Template


class ConfigTemplateBuilder:
    def __init__(self, template_dir: str = "templates"):
        self._template_path = Path(template_dir)
        self._set_env()

    def _set_env(self) -> Environment:
        """Create a jinja2 environment with the given template directory.

        :return: jinja2 environment
        :rtype: Environment
        """
        env = Environment(
            loader=FileSystemLoader(self._template_path),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
            extensions=["jinja2.ext.do"],
        )
        self.env = env

    def _get_template_path(self) -> Path:
        return self._template_path

    @property
    def template_path(self) -> Path:
        return self._get_template_path()

    @template_path.setter
    def template_path(self, template_path: str):
        if Path(template_path).is_dir():
            self._template_path = Path(template_path)
            self._set_env()

    def _render(self, template: Template, context: Any) -> str:
        return template.render(context)

    def render_template(
        self, template_name_or_list: Union[str, List[str]], context: Any
    ) -> str:
        """Render a template with the given context.

        :param template_name_or_list: name of the template to render or a list of template names.
            If a list, the first template that can be rendered will be used.
        :type template_name_or_list: Union[str, List[str]]
        :param context: The data to render the template with.
        :type context: Any
        :return: templated string
        :rtype: str
        """
        template = self.env.get_or_select_template(template_name_or_list)
        return self._render(template, context)
