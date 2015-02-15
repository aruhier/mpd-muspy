#!/usr/bin/python

import mpd
from mpd_muspy.artist_db import Artist_db

SERVER = "localhost"
PORT = 6600
ARTISTS_JSON = "artists.json"


def connect(mpdclient):
    """
    Handle connection to the mpd server
    """
    mpdclient.connect(SERVER, PORT)


artist_db = Artist_db(jsonpath=ARTISTS_JSON)
mpdclient = mpd.MPDClient()
connect(mpdclient)
try:
    artists = set(str(artist).lower() for artist in mpdclient.list("artist")
                  if artist != "")
except mpd.ConnectionError:
    connect(mpdclient)
    artists = set(str(artist).lower() for artist in mpdclient.list("artist")
                  if artist != "")

artists_removed, artists_added = artist_db.merge(artists)
artist_db.save()

print(len(artists_added), "artist(s) added")
print(len(artists_removed), "artist(s) removed")
print("Total: ", len(artists_added) + len(artists_removed),
      "artist(s) updated")
