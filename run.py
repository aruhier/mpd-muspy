#!/usr/bin/python

import mpd
import sys
from mpd_muspy.artist_db import Artist_db
try:
    from config import ARTISTS_JSON, SERVER, PORT
except ImportError:
    print("Configuration file config.py not found. Please copy the "
          "config.py.default as config.py.", file=sys.stderr)
    sys.exit(1)
from mpd_muspy.muspy_api import Muspy_api


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
non_uploaded_artists = artist_db.get_non_uploaded()

print(len(non_uploaded_artists), "artist(s) non uploaded on muspy")
print(len(artists_added), "artist(s) added")
print(len(artists_removed), "artist(s) removed")
print("Total: ", len(artists_added) + len(artists_removed),
      "artist(s) updated")

muspy_api = Muspy_api()
for artist in non_uploaded_artists:
    try:
        muspy_api.add_artist(artist)
        artist_db.mark_as_uploaded(artist)
        print("Artist:", artist, ". Done...")
    except Exception as e:
        print(e)
        pass
    finally:
        artist_db.save()
