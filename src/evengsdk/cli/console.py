from typing import Dict, List, Union, Any, Literal
import sys

from rich.console import Console
from rich.theme import Theme
from rich.traceback import install

from evengsdk.plugins.display import format_output
from evengsdk.exceptions import EvengHTTPError, EvengApiError

# Install rich traceback as default traceback handler
install(show_locals=True, max_frames=10)

console_theme = Theme({"info": "cyan", "warning": "magenta", "danger": "bold red"})


class ConsolePrinter(Console):
    def __init__(self):
        super().__init__(theme=console_theme)

    def print_output(self, plugin: str, data: Dict, *args, **kwargs) -> None:
        """Print output based on plugin"""
        header = kwargs.pop("header", None)
        output = format_output(plugin, data, *args, **kwargs)

        if not output:
            sys.exit(0)

        try:
            if plugin == "json":
                self.print_json(output)
                sys.exit(0)

            if plugin == "text" and header:
                self.print(header, style="info")

            self.print(output)
            sys.exit(0)
        except Exception:
            self.console.print_exception(show_locals=True)

    def print_error(self, message: str) -> None:
        self.print(f"[danger]ERROR:[/danger] {message}")
        sys.exit(1)

    def print_exc(self) -> None:
        self.print_exception(show_locals=True, max_frames=10)


console = ConsolePrinter()


def cli_print_output(
    plugin: Literal["json", "text", "table"],
    data: Union[Dict, List, str],
    *args,
    **kwargs,
):
    """
    Print based on the plugin type
    """
    try:
        console.print_output(plugin, data, *args, **kwargs)
    except (EvengHTTPError, EvengApiError) as e:
        msg = f"{e}"
        if "Cannot find node" in msg:
            msg = "could not find specified node in lab"
        console.print_error(msg)


def cli_print(output: Any, *args, **kwargs):
    """Generic print function"""
    try:
        console.print(output, *args, **kwargs)
    except (EvengHTTPError, EvengApiError) as e:
        console.print_error(f"{e}")


def cli_print_error(output: Any):
    """Generic print function"""
    console.print_error(f"{output}")
