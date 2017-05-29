#!/usr/bin/env python3

import argparse
from mpd_muspy import _release_name, _version
from mpd_muspy.sync import run as run_sync


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sync artists of your MPD database with your MuSpy account"
    )

    parser.add_argument(
        "-c", "--clean",
        help=(
            "drop everything of the database to start syncing from a fresh one"
        ), dest="clean", action="store_true"
    )

    parser.add_argument(
        "--version", action="version",
        version="{} {}".format(_release_name, _version)
    )

    parser.set_defaults(func=sync)

    args = parser.parse_args()
    args.func(parsed_args=args)


def sync(parsed_args):
    return run_sync(clean=parsed_args.clean)


if __name__ == "__main__":
    parse_args()
