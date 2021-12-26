from jinja2 import Environment, PackageLoader


def build_inventory(eve_host, lab_path, nodes):
    for node in nodes:
        node["console_port"] = node["url"].split(":")[2]
        node["console_server"] = eve_host

    template_data = {
        "lab_path": lab_path,
        "eve_host": eve_host,
        "groups": {"all": nodes},
    }
    env = Environment(loader=PackageLoader("evengsdk", "templates"))
    template = env.get_template("inventory.ini.j2")
    inventory = template.render(template_data)
    return inventory
