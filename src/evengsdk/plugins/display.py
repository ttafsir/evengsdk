# -*- coding: utf-8 -*-
# standard lib imports
import html
import json as jsonlib
from typing import List, Dict, Union

# third party lib imports
import click
from tabulate import tabulate

# package imports


_PLUGINS = {}


def register_plugin(func):
    _PLUGINS[func.__name__] = func
    return func


def display(plugin: str, data: Union[List, Dict], *args, **kwargs) -> str:
    if plugin in _PLUGINS:
        return _PLUGINS[plugin](data, *args, **kwargs)
    else:
        return TypeError(f"{plugin} is not a supported display plugin")


@register_plugin
def json(data, *args, **kwargs):
    indent = kwargs.get("indent", 2)
    fg_color = kwargs.get("fg_color", "bright_white")
    return click.style(jsonlib.dumps(data, indent=indent), fg=fg_color)


@register_plugin
def table(data, *args, **kwargs):
    header = kwargs.get("header")
    display_table = []
    fmt = kwargs.get("tablefmt", "grid")

    if isinstance(data, dict) and header:
        display_table = iter(data.items())
        return tabulate(display_table, headers=header, tablefmt=fmt)

    elif isinstance(data, list):
        for item in data:
            # trim dict keys to match header passed in
            keys_to_drop = set(item) - set(header) if header else set()
            for key in keys_to_drop:
                if isinstance(item, dict):
                    del item[key]
            display_table.append(item)
    return tabulate(display_table, headers="keys", tablefmt=fmt)


def _dict_to_string(obj: dict) -> str:
    for key, val in obj.items():
        if isinstance(val, str):
            escaped_val = html.unescape(val)
            yield f"  {key}: {escaped_val}\n"
        elif isinstance(val, int):
            yield f"  {key}: {val}\n"


@register_plugin
def text(
    data: Dict,
    header: List[str] = [],
    fg_color: str = "bright_white",
    record_header: str = "",
    record_header_fg_color: str = "yellow",
) -> str:
    """Generate human readable output for passed object

    Args:
        data (Dict): dict or list of dicts to format as output
        header (List[str], optional): list of keys to output. Defaults to [].
        fg_color (str, optional): fg color for output. Defaults to
            "bright_white".
        record_header (str, optional): Header to display for each record in a
            list. Defaults to "".

    Returns:
        str: formatted output string
    """
    string_output = "\n"

    if isinstance(data, dict):
        for ln in _dict_to_string(data):
            string_output += ln

    elif isinstance(data, list):
        for obj in data:
            if record_header:
                string_output += click.style(
                    obj[record_header].upper(), fg=record_header_fg_color
                )
                string_output += "\n"

            if isinstance(obj, dict):
                for ln in _dict_to_string(obj):
                    string_output += ln
                string_output += "\n"
    else:
        string_output += str(data)
    return click.style(string_output, fg=fg_color)
