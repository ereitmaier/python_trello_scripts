"""
env_loader.py
-------------
Helper module to load environment variables (such as KEY and TOKEN)
from a local environment file (e.g., '.trello_auth').
"""

import os
import sys

def load_env_file(filepath=".trello_auth"):
    """Loads KEY and TOKEN variables from a bash source or env file into os.environ.

    Args:
        filepath (str): Path to environment file. Defaults to '.trello_auth'.

    Raises:
        SystemExit: Exits the program if the file is missing.
    """
    if not os.path.exists(filepath):
        print(
            f"Error: The file '{filepath}' was not found.",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            # Ignore empty lines or comments
            if not line or line.startswith("#"):
                continue
            # Remove optional 'export ' prefixes and surrounding quotes
            if line.startswith("export "):
                line = line[7:]
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip("\"'")