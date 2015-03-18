#!/usr/bin/python
# Author: Anthony Ruhier

import __main__
import os
import sys

# Check that the configuration exists
try:
    _current_dir = os.path.dirname(__main__.__file__)
except AttributeError:
    _current_dir = os.getcwd()
if not os.path.exists(os.path.join(_current_dir, "config.py")):
    print("Configuration file config.py not found. Please copy the "
          "config.py.default as config.py.", file=sys.stderr)
    sys.exit(1)

_version = "0.1.1"
_release_name = "mpd_muspy"
