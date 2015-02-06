#!/usr/bin/python

import mpd

SERVER = "localhost"
PORT = 6600


def connect(mpdclient):
    """
    Handle connection to the mpd server
    """
    mpdclient.connect(SERVER, PORT)


mpdclient = mpd.MPDClient()
connect(mpdclient)
bands = set(str(artist).lower() for artist in mpdclient.list("artist")
            if artist != "")
print(bands)
