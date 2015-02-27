#!/usr/bin/python
# Author: Anthony Ruhier

import os
import mpd
import threading
from .muspy_api import Muspy_api
from .artist_db import Artist_db
from . import _current_dir
from config import ARTISTS_JSON, SERVER, PORT

ARTISTS_JSON = os.path.join(_current_dir, ARTISTS_JSON)


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


def chunks(l, n):
    """
    Yield successive n-sized chunks from l.
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]


def mpd_get_artists(artist_db, mpdclient):
    mpdclient.connect(SERVER, PORT)
    try:
        artists = set(str(artist).lower()
                      for artist in mpdclient.list("artist") if len(artist))
    except mpd.ConnectionError:
        mpdclient.connect(SERVER, PORT)
        artists = set(str(artist).lower()
                      for artist in mpdclient.list("artist") if len(artist))
    return artists


def start_threads(non_uploaded_artists, artist_db):
    nb_threads = 5
    lock = threading.Lock()
    threads = []
    muspy_api = Muspy_api()
    nb_artists_by_split = int(len(non_uploaded_artists) / nb_threads)
    for l in chunks(non_uploaded_artists, nb_artists_by_split):
        thread = SyncThread(artists=l, artist_db=artist_db,
                            muspy_api=muspy_api, lock=lock)
        thread.daemon = True
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def run():
    artist_db = Artist_db(jsonpath=ARTISTS_JSON)
    mpdclient = mpd.MPDClient()

    artists = mpd_get_artists(artist_db, mpdclient)
    artists_removed, artists_added = artist_db.merge(artists)
    artist_db.save()
    non_uploaded_artists = artist_db.get_non_uploaded()
    artists = None

    print(len(non_uploaded_artists), "artist(s) non uploaded on muspy")
    print(len(artists_added), "artist(s) added")
    print(len(artists_removed), "artist(s) removed")

    start_threads(non_uploaded_artists, artist_db)
    print("Done: ",
          len(non_uploaded_artists) - len(artist_db.get_non_uploaded()),
          "artist(s) updated")
