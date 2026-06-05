"""
Entrypoint for sealocs command-line interface (CLI).
"""

import click

from .tasks.commands import command_group as tasks_group


@click.group()
def entrypoint() -> None:
    """Sealocs main CLI."""
    pass


entrypoint.add_command(tasks_group, name="tasks")


def main() -> None:
    """Main function running the CLI."""
    entrypoint()


if __name__ == "__main__":
    main()
