# -*- coding: utf-8 -*-
# standard lib imports
import html
import json as jsonlib
from typing import List, Dict, Union, Any

# third party lib imports
from rich.table import Table

# package imports


_PLUGINS = {}


def register_plugin(func):
    _PLUGINS[func.__name__] = func
    return func


def format_output(plugin: str, data: Union[List, Dict], *args, **kwargs) -> str:
    if plugin in _PLUGINS:
        return _PLUGINS[plugin](data, *args, **kwargs)
    else:
        return TypeError(f"{plugin} is not a supported display plugin")


@register_plugin
def json(data, *args, **kwargs):
    indent = kwargs.get("indent", 2)
    if isinstance(data, dict):
        return jsonlib.dumps(data.get("data", data), indent=indent)
    return jsonlib.dumps(data, indent=indent)


@register_plugin
def table(data, *args, **kwargs):
    table = Table(
        title=kwargs.get("table_title", None),
        show_header=kwargs.get("show_header", True),
    )
    table_header_and_opts = kwargs.get("table_header")  # tuples of (header, opts)
    keys = data["data"][0].keys()  # keys from first item in data

    # use the first item in table_header_and_opts to set the header; default to keys in data
    table_header = [x[0] for x in table_header_and_opts] or list(keys)

    # determine which keys to display
    keys_to_drop = (
        set(keys) - {x.lower() for x in table_header} if table_header else set()
    )
    table_data = data.get("data", [])
    display_table = []

    if isinstance(table_data, list):
        for item in table_data:
            for key in keys_to_drop:
                if isinstance(item, dict):
                    del item[key]
            display_table.append(item)

    if table_header:
        for col_name, col_options in table_header_and_opts:
            formatted_col_name = col_name.title().replace("_", " ")
            table.add_column(formatted_col_name, **col_options)

    for row in display_table:
        table.add_row(*[f"{row[key.lower()]}" for key in table_header])
    return table


def _dict_to_string(obj: dict) -> str:
    for key, val in obj.items():
        if isinstance(val, str):
            escaped_val = html.unescape(val)
            yield f"  {key}: {escaped_val}\n"
        elif isinstance(val, int):
            yield f"  {key}: {val}\n"


@register_plugin
def text(
    data: Any,
    record_header_key: str = "",
    *args,
    **kwargs,
) -> str:
    """Format data as text"""
    string_output = ""
    display_data = data.get("data")

    # sometimes we just have a status message
    if display_data is None and data.get("message") is not None:
        string_output = f"{data.get('status')}: {data.get('message')}"
        return string_output

    # render dicts as text output
    if isinstance(display_data, dict):
        for ln in _dict_to_string(display_data):
            string_output += ln
        return string_output

    # render lists as text output, if a record_header_key is passed
    # we retrieve the value of that key from each record and use it as the header in the output text
    elif isinstance(display_data, list):
        for obj in display_data:
            if record_header_key:
                string_output += (
                    f"[bold][cyan]{obj.get(record_header_key).upper()}[/cyan][/bold]"
                )
                string_output += "\n"

            if isinstance(obj, dict):
                for ln in _dict_to_string(obj):
                    string_output += f"[white]{ln}[/white]"
                string_output += "\n"
        return string_output
    return data
