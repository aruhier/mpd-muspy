#!/usr/bin/python

import mpd
import threading
import sys
from mpd_muspy.artist_db import Artist_db
try:
    from config import ARTISTS_JSON, SERVER, PORT
except ImportError:
    print("Configuration file config.py not found. Please copy the "
          "config.py.default as config.py.", file=sys.stderr)
    sys.exit(1)
from mpd_muspy.muspy_api import Muspy_api


class SyncThread(threading.Thread):
    """
    Launch synchronisation with muspy
    """
    def __init__(self, artists, artist_db, muspy_api, lock):
        super().__init__()
        self.artists = artists
        self.artist_db = artist_db
        self.muspy_api = muspy_api
        self.lock = lock

    def run(self):
        for artist in self.artists:
            try:
                self.muspy_api.add_artist(artist)
                self.lock.acquire()
                self.artist_db.mark_as_uploaded(artist)
                print("Artist:", artist, ". Done...")
                self.lock.release()
            except Exception as e:
                print(e)
                pass
            finally:
                self.lock.acquire()
                self.artist_db.save()
                self.lock.release()


def connect(mpdclient):
    """
    Handle connection to the mpd server
    """
    mpdclient.connect(SERVER, PORT)


def chunks(l, n):
    """
    Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]


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

lock = threading.Lock()
threads = []
muspy_api = Muspy_api()
for l in chunks(non_uploaded_artists, 10):
    thread = SyncThread(artists=l, artist_db=artist_db, muspy_api=muspy_api,
                        lock=lock)
    thread.daemon = True
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join()
