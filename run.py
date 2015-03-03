#!/usr/bin/python

import getopt
import sys
from mpd_muspy.sync import run as run_sync


def usage():
    print("Synchronize artists on your MuSpy account from the ones in your "
          "MPD database.\n")
    print("sync.py [options]")
    print("Options:")
    print("\t-h, --help: Print this help message")


def handle_arguments(opts):
    """
    Handle arguments
    """
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit(0)
        else:
            print("Option " + o + " doesn't exists\n")
            usage()


if __name__ == "__main__":
    # Arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h",
                                   ["help"])
        handle_arguments(opts)
    except getopt.GetoptError as e:
        print(e)
        usage()
        exit(1)
    run_sync()
