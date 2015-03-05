#!/usr/bin/python
# Author: Anthony Ruhier

import os
import mpd
import multiprocessing
from multiprocessing.managers import BaseManager
from .muspy_api import Muspy_api
from .artist_db import Artist_db
from . import _current_dir
from config import ARTISTS_JSON, SERVER, PORT

ARTISTS_JSON = os.path.join(_current_dir, ARTISTS_JSON)
NB_MULTIPROCESS = 3


class SyncManager(BaseManager):
    pass

SyncManager.register('Artist_db', Artist_db)
SyncManager.register('Muspy_api', Muspy_api)


def chunks(l, n):
    """
    Yield successive n-sized chunks from l.

    :param l: list to split
    :param n: number of elements wanted in each list split
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]


def mpd_get_artists(mpdclient):
    """
    Get artists from MPD

    :param mpdclient: connection with MPD
    :type mpdclient: mpd.MPDClient()
    """
    mpdclient.connect(SERVER, PORT)
    try:
        artists = set(str(artist).lower()
                      for artist in mpdclient.list("artist") if len(artist))
    except mpd.ConnectionError:
        mpdclient.connect(SERVER, PORT)
        artists = set(str(artist).lower()
                      for artist in mpdclient.list("artist") if len(artist))
    return artists


def process_task(artists, artists_nb, artist_db, lock, counter):
    """
    Function launched by each process

    Add artists on muspy and marks it in the artists database.

    :param artists: list of artists split for this process
    :type artists: list
    :param artists_nb: total artists to upload. Different of len(artists), here
                       it is the total number of artists of all processes.
    :type artists: int
    :param artist_db: database of artists, in the shared memory
    :type artist_db: SyncManager.Artist_db()
    :param muspy_api: custom api for muspy
    :type muspy_api: Muspy_api()
    :param lock: lock shared between the processes
    :type lock: multiprocessing.Lock
    :param counter: integer in the shared memory
    :type counter: multiprocessing.Value("i")
    """
    muspy_api = Muspy_api()
    for artist in artists:
        error = ""
        try:
            muspy_api.add_artist(artist)
            with lock:
                artist_db.mark_as_uploaded(artist)
                artist_db.save()
        except Exception as e:
            error = "Error: " + str(e)
            pass
        finally:
            with lock:
                counter.value += 1
            print("[", counter.value, "/", artists_nb, "]:", artist.title())
            if error:
                print(error)


def start_process(non_uploaded_artists, artist_db):
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
    mpdclient = mpd.MPDClient()

    artists = mpd_get_artists(mpdclient)
    artists_removed, artists_added = artist_db.merge(artists)
    artist_db.save()
    non_uploaded_artists = artist_db.get_non_uploaded()
    artists = None

    print(len(non_uploaded_artists), "artist(s) non uploaded on muspy")
    print(len(artists_added), "artist(s) added")
    print(len(artists_removed), "artist(s) removed")

    print("\n   Start syncing  \n =================\n")
    start_process(non_uploaded_artists, artist_db)
    print("Done: ",
          len(non_uploaded_artists) - len(artist_db.get_non_uploaded()),
          "artist(s) updated")
