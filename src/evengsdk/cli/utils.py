# -*- coding: utf-8 -*-
import html
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List

import click

from evengsdk.cli.console import console
from evengsdk.client import EvengLoginError


def get_client(ctx):
    client = ctx.obj.client
    try:
        client.login(ctx.obj.username, ctx.obj.password)
        return client
    except (EvengLoginError) as err:
        console.print_error(err)


def to_human_readable(obj: Dict, keys: List[str] = []) -> str:
    """Generate human readable output for passed object

    Args:
        obj (dict): Object to format
        keys (list[str]): list of keys to print output for

    Returns:
        str: formatted string output
    """
    keys_to_drop = set(obj) - set(keys) if keys else set()
    for key in keys_to_drop:
        del obj[key]

    for key, val in obj.items():
        if isinstance(val, str):
            escaped_val = html.unescape(val)
            yield f"  {key}: {escaped_val}"
        elif isinstance(val, int):
            yield f"  {key}: {val}"


def thread_executor(func, items):
    futures = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for future in executor.map(func, items):
            futures.append(future)
    return futures


def display_status(resp: Dict):
    if resp:
        msg = resp.get("message")
        fg_color = "green" if resp["status"] == "success" else "red"
        click.secho(msg, fg=fg_color)
        sys.exit(0)
    err = click.style("Unknown Error: no status received", fg="red")
    sys.exit(err)


def get_active_lab(eveng_directory: str):
    """get active lab from eve-ng directory

    Args:
        eveng_directory (str): path to eve-ng directory

    Returns:
        [str]: return lab path or None
    """
    # ensure directory exists
    Path(eveng_directory).mkdir(exist_ok=True)

    # path to active lab file
    active_lab_filepath = Path(eveng_directory) / "active"

    if active_lab_filepath.exists():
        return active_lab_filepath.read_text()
    return os.environ.get("EVE_NG_LAB_PATH")
