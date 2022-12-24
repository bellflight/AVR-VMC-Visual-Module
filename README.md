# AVR-VMC-Visual-Module

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Build Visual Module](https://github.com/bellflight/AVR-VMC-Visual-Module/actions/workflows/build.yml/badge.svg)](https://github.com/bellflight/AVR-VMC-Visual-Module/actions/workflows/build.yml)

The Visual Inertial Orientation (VIO) module is responsible for capturing data
from the stereoscopic tracking camera, and converting it into global-ish coordinates.

This module considers wherever it is started as "0,0,0" and thus the drone's movements
are relative to that. Because PX4 only thinks in global coordinates, this module then
uses a hardcoded latitude and longitude to convert the data into global coordinates.
They;re not true global coordinates, however, as they’re still relative to
where it was started.

This module is the core of the AVR "secret sauce" to enable GPS-denied
stabilized flight.

## Developer Notes

ZED camera config files are stored in `/usr/local/zed/settings/`. This directory
should be persisted via a bind-mount.
