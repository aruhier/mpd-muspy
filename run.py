#!/usr/bin/python

import getopt
import sys
from mpd_muspy import _version
from mpd_muspy.sync import run as run_sync


def usage():
    print("MPD MuSpy", _version)
    print("Synchronize artists on your MuSpy account from the ones in your "
          "MPD database.\n")
    print("sync.py [options]")
    print("Options:")
    print("\t-c, --clean: Drop everything in the database to start syncing "
          "from a clean one")
    print("\t-h, --help: Print this help message")


def handle_arguments(opts):
    """
    Handle arguments
    """
    kwargs = dict()
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        elif o in ("-c", "--clean"):
            kwargs["clean"] = True
        else:
            print("Option " + o + " doesn't exists\n")
            usage()
    return kwargs


if __name__ == "__main__":
    # Arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc",
                                   ["help", "clean"])
        kwargs = handle_arguments(opts)
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(1)
    run_sync(**kwargs)
