# AVR-VMC-Visual-Module

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Build Visual Module](https://github.com/bellflight/AVR-VMC-Visual-Module/actions/workflows/build.yml/badge.svg)](https://github.com/bellflight/AVR-VMC-Visual-Module/actions/workflows/build.yml)

The Visual Inertial Orientation (VIO) module is responsible for capturing data
from the stereoscopic tracking camera, and converting it into global-ish coordinates.

This module considers wherever it is started as "0,0,0" and thus the drone's movements
are relative to that. Because PX4 only thinks in global coordinates,
this module then uses a hardcoded latitude and longitude to convert the data
into global coordinates. They're not true global coordinates, however, as they’re
still relative to where it was started.

This module is the core of the AVR "secret sauce" to enable GPS-denied
stabilized flight.

## Development

It's assumed you have a version of Python installed from
[python.org](https://python.org) that is the same or newer as
defined in the [`Dockerfile`](Dockerfile).

First, install [Poetry](https://python-poetry.org/):

```bash
python -m pip install pipx --upgrade
pipx ensurepath
pipx install poetry
# (Optionally) Add pre-commit plugin
poetry self add poetry-pre-commit-plugin
```

Now, you can clone the repo and install dependencies:

```bash
git clone https://github.com/bellflight/AVR-VMC-Visual-Module
cd AVR-VMC-Visual-Module
poetry install --sync
poetry run pre-commit install --install-hooks
```

Run

```bash
poetry shell
```

to activate the virtual environment.

### Notes

ZED camera config files are stored in `/usr/local/zed/settings/`. This directory
should be persisted via a bind-mount.
