# -*- coding: utf-8 -*-
# standard lib imports
import html
import json as jsonlib
from typing import List, Dict, Union, Any

# third party lib imports
from tabulate import tabulate

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
    data: Any,
    *args,
    **kwargs,
) -> str:
    """Format data as text"""
    if isinstance(data, dict):
        string_output = ""
        data_dict = data.get("data")
        if data_dict:
            for ln in _dict_to_string(data_dict):
                string_output += ln
            return string_output
        elif data.get("message"):
            string_output = f"{data.get('status')}: {data.get('message')}"
            return string_output
    return data
