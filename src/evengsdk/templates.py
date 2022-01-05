# -*- coding: utf-8 -*-
from jinja2 import BaseLoader, Environment


def render_template(templateIO, data):
    """
    Render a Jinja template with supplied data

    Parameters:
        templateIO (str): jinja2 formatted string template
        data (dict): data to be rendered to template

    Returns:
        str: rendered string
    """
    env = Environment(loader=BaseLoader(), trim_blocks=True, lstrip_blocks=True)
    template = env.from_string(templateIO)
    return template.render(data)


def render_from_path(path, data):
    """
    Load template string from given path and render

    Parameters:
        path (str): path to template
        data (dict): data to be rendered to template

    Returns:
        str: rendered string
    """
    with open(path, "r") as f:
        template_string = f.read()
        return render_template(template_string, data)
