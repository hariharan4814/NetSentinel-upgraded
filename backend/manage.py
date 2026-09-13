"""Backend commands; use a separate environment from the standalone sensor."""
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    selected_settings = os.environ["DJANGO_SETTINGS_MODULE"]
    for index, argument in enumerate(sys.argv[1:], 1):
        if argument.startswith("--settings="):
            selected_settings = argument.split("=", 1)[1]
        elif argument == "--settings" and index + 1 < len(sys.argv):
            selected_settings = sys.argv[index + 1]
    if (selected_settings == "config.test_settings" and
            (len(sys.argv) < 2 or sys.argv[1] not in {"test", "check", "makemigrations"})):
        raise SystemExit("SQLite settings are restricted to test, check and makemigrations commands.")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
