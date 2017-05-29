#!/usr/bin/python
# Author: Anthony Ruhier

import os
import sys

try:
    _current_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "../"
    )
except AttributeError:
    _current_dir = os.getcwd()

_version = "0.2.1"
_release_name = "mpd_muspy"
