import click


output_option = click.option(
    "--output",
    type=click.Choice(["json", "text", "table"]),
    default="table",
)


def list_sub_command(subcommand):
    for decorator in reversed(
        (
            click.command(name="list"),
            output_option,
        )
    ):
        subcommand = decorator(subcommand)
    return subcommand


def list_command(command):
    for decorator in reversed((output_option,)):
        command = decorator(command)
    return command
