import os
import sys

def load_env_file(filepath=".trello_auth"):
    """Laadt KEY en TOKEN uit een bash source/env bestand."""
    if not os.path.exists(filepath):
        print(
            f"Error: Het bestand '{filepath}' is niet gevonden.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            # Negeer lege regels of commentaar
            if not line or line.startswith("#"):
                continue
            # Verwijder optionele 'export ' en quotes rond variabelen
            if line.startswith("export "):
                line = line[7:]
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip("\"'")