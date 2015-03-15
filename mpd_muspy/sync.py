#!/usr/bin/python
# Author: Anthony Ruhier

import os
import mpd
import multiprocessing
from multiprocessing.managers import BaseManager
from . import _current_dir
from .artist_db import Artist_db
from .muspy_api import Muspy_api
from .presync import presync
from .tools import chunks
from config import ARTISTS_JSON

ARTISTS_JSON = os.path.join(_current_dir, ARTISTS_JSON)
NB_MULTIPROCESS = 5


class SyncManager(BaseManager):
    pass

SyncManager.register('Artist_db', Artist_db)
SyncManager.register('MPDClient', mpd.MPDClient)


def process_task(artists, artists_nb, artist_db, lock, counter):
    """
    Function launched by each process

    Add artists on muspy and marks it in the artists database.

    :param artists: list of artists split for this process
    :type artists: list
    :param artists_nb: total artists to upload. Different of len(artists), here
                       it is the total number of artists of all processes.
    :type artists_nb: int
    :param artist_db: database of artists, in the shared memory
    :type artist_db: SyncManager.Artist_db()
    :param lock: lock shared between the processes
    :type lock: multiprocessing.Lock
    :param counter: integer in the shared memory
    :type counter: multiprocessing.Value("i")
    """
    muspy_api = Muspy_api()
    for artist in artists:
        error = ""
        try:
            if "mbid" in artist.keys():
                muspy_api.add_artist_mbid(artist["mbid"])
                with lock:
                    artist_db.mark_as_uploaded(artist["name"])
                    artist_db.save()
            else:
                error = "Doesn't have a musicbrainz ID"
        except Exception as e:
            error = "Error: " + str(e)
            pass
        finally:
            with lock:
                counter.value += 1
            print("[", counter.value, "/", artists_nb, "]:",
                  artist["name"].title())
            if error:
                print(error)


def start_pool(non_uploaded_artists, artist_db):
    """
    Initialize the synchronization in several process

    :param non_uploaded_artists: list of artists name to upload
    :type non_uploaded_artists: list
    :param artist_db: Artist_db() object in the shared memory
    :type artist_db: SyncManager.Artist_db
    """
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    counter = manager.Value("i", 0)
    artists_nb = len(non_uploaded_artists)
    artists_nb_by_split = int(artists_nb / NB_MULTIPROCESS)
    pool = multiprocessing.Pool()
    for l in chunks(non_uploaded_artists, artists_nb_by_split):
        pool.apply_async(
            process_task,
            kwds={"artists": l, "artists_nb": artists_nb,
                  "artist_db": artist_db, "lock": lock, "counter": counter}
        )
    pool.close()
    pool.join()


def run():
    process_manager = SyncManager()
    process_manager.start()
    artist_db = process_manager.Artist_db(jsonpath=ARTISTS_JSON)
    mpdclient = process_manager.MPDClient()
    non_uploaded_artists = presync(artist_db, mpdclient)

    print("\n   Start syncing\n =================\n")
    start_pool(non_uploaded_artists, artist_db)
    print("Done: ",
          len(non_uploaded_artists) -
          len(artist_db.get_artists(uploaded=False)),
          "artist(s) updated")
    process_manager.shutdown()
