#!/usr/bin/env python3

"""
osdeps retrieves the list of packages needed for a given distro
across the different Archivematica components.

Usage: ./osdeps.py [distro] [stage]

  distro   (required) Distro name, e.g. "Ubuntu-18"
  stage    (requried) Stage number, e.g. "1", "2", ...

Typically, we'll use stage "1". However, some distros require packages to be
installed in multiple groups.

In combination with apt, users can do something like the following in order to
automatically install the osdeps dependencies:

    ./osdeps.py Ubuntu-18 1 | xargs apt-get install
"""

import json
import sys
from pathlib import Path

OSDEPS_DIRS = ("dashboard/osdeps", "MCPServer/osdeps", "MCPClient/osdeps")

try:
    distro = sys.argv[1]
except IndexError:
    sys.exit('Missing argument: distro, e.g. "Ubuntu-18"')

try:
    stage = int(sys.argv[2])
except (IndexError, ValueError):
    sys.exit('Missing argument: stage, e.g. "1"')

src_dir = Path(__file__).parents[1] / "src"

packages = set()

for osdeps_dir in OSDEPS_DIRS:
    osdeps = src_dir / osdeps_dir / f"{distro}.json"
    if not osdeps.is_file():
        sys.exit(f"{str(osdeps)} not found")
    try:
        document = json.loads(osdeps.read_bytes())
    except json.decoder.JSONDecodeError as err:
        sys.exit(f"Error reading {str(osdeps)}: {err}")
    key = "osdeps_packages" if stage == 1 else f"osdeps_packages_{stage}"
    if key not in document:
        continue
    packages.update([item["name"] for item in document[key]])

if not packages:
    sys.exit("No packages needed.")

print("\n".join(packages))
