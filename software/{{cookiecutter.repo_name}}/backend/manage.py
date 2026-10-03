"""Django's command line, defaulting to the development settings."""

import os
import sys


def main() -> None:
    """Run a management command with ``config.settings.dev`` by default."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    # pylint: disable-next=import-outside-toplevel
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
