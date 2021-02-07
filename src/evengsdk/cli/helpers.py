# -*- coding: utf-8 -*-
from typing import Dict, List


def to_human_readable(
    obj: Dict,
    keys: List[str] = []
) -> str:
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
            yield f'  {key}: {val:>4s}'
        elif isinstance(val, int):
            yield f'  {key}: {val:>4d}'