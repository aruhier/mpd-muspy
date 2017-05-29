#!/usr/bin/python
# Author: Anthony Ruhier

import appdirs
import os
import mpd
import multiprocessing
from multiprocessing.managers import BaseManager
from . import _release_name
from .artist_db import Artist_db
from .muspy_api import Muspy_api
from .presync import presync
from .tools import chunks, get_config

config = get_config()
from config import ARTISTS_JSON

ARTISTS_JSON = os.path.join(
    appdirs.user_data_dir(_release_name), ARTISTS_JSON
)
NB_MULTIPROCESS = 5


class SyncManager(BaseManager):
    pass


SyncManager.register('Artist_db', Artist_db)
SyncManager.register('MPDClient', mpd.MPDClient)


def process_add_artists(artists, artists_nb, artist_db, lock, error_nb,
                        counter):
    """
    Function launched by each process to add artists on muspy

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
                with lock:
                    error_nb.value += 1
        except Exception as e:
            error = "Error: " + str(e)
            with lock:
                error_nb.value += 1
        finally:
            with lock:
                counter.value += 1
            print("[", counter.value, "/", artists_nb, "]:",
                  artist["name"].title())
            if error:
                print(error)


def process_del_artists(artists, artists_nb, lock, error_nb, counter):
    """
    Function launched by each process to add artists on muspy

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
            muspy_api.del_artist_mbid(artist[1])
        except Exception as e:
            error = "Error: " + str(e)
            with lock:
                error_nb.value += 1
        finally:
            with lock:
                counter.value += 1
            print("[", counter.value, "/", artists_nb, "]:",
                  artist[0].title())
            if error:
                print(error)


def start_pool_del(remove_of_muspy):
    """
    Initialize the synchronization in several process to remove of muspy

    :param non_uploaded_artists: list of artists name to upload
    :type non_uploaded_artists: list
    :param artist_db: Artist_db() object in the shared memory
    :type artist_db: SyncManager.Artist_db
    """
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    error = manager.Value("i", 0)
    counter = manager.Value("i", 0)
    artists_nb = len(remove_of_muspy)
    artists_nb_by_split = int(artists_nb / NB_MULTIPROCESS)
    pool = multiprocessing.Pool()

    try:
        for l in chunks(remove_of_muspy, artists_nb_by_split):
            pool.apply_async(
                process_del_artists,
                kwds={"artists": l, "artists_nb": artists_nb,
                      "lock": lock, "error_nb": error,
                      "counter": counter}
            )
        pool.close()
    except Exception as e:
        pool.terminate()
        raise e
    finally:
        pool.join()
    return error.value


def start_pool_add(non_uploaded_artists, artist_db):
    """
    Initialize the synchronization in several process to add artist on muspy

    :param non_uploaded_artists: list of artists name to upload
    :type non_uploaded_artists: list
    :param artist_db: Artist_db() object in the shared memory
    :type artist_db: SyncManager.Artist_db
    """
    manager = multiprocessing.Manager()
    lock = manager.Lock()
    error = manager.Value("i", 0)
    counter = manager.Value("i", 0)
    artists_nb = len(non_uploaded_artists)
    artists_nb_by_split = int(artists_nb / NB_MULTIPROCESS)
    pool = multiprocessing.Pool()

    try:
        for l in chunks(non_uploaded_artists, artists_nb_by_split):
            pool.apply_async(
                process_add_artists,
                kwds={"artists": l, "artists_nb": artists_nb,
                      "artist_db": artist_db, "lock": lock, "error_nb": error,
                      "counter": counter}
            )
        pool.close()
        pool.join()
    except Exception as e:
        pool.terminate()
        pool.join()
        raise e
    return error.value


def run(clean=False):
    """
    Run synchronization. If clean parameter is specified, remove everything in
    the current database, to start on a clean one.

    :param clean: boolean about if starting a clean synchronization (drop the
        db) or not.
    :type clean: boolean
    """
    process_manager = SyncManager()
    process_manager.start()
    if clean:
        artist_db = process_manager.Artist_db(
            jsonpath=ARTISTS_JSON, artists={})
        artist_db.save()
    else:
        artist_db = process_manager.Artist_db(jsonpath=ARTISTS_JSON)
    mpdclient = process_manager.MPDClient()
    try:
        non_uploaded_artists, remove_of_muspy = presync(artist_db, mpdclient)

        print("\n   Start syncing\n =================\n")
        error = start_pool_add(non_uploaded_artists, artist_db)
    except Exception as e:
        artist_db.save()
        raise e

    if len(remove_of_muspy):
        print("\nRemoving of Muspy artists who do not exist in mpd "
              "anymore...\n")
        error += start_pool_del(remove_of_muspy)
    msg = ("Done: " +
           str(len(non_uploaded_artists) + len(remove_of_muspy) -
               len(artist_db.get_artists(uploaded=False))) +
           " artist(s) updated")
    if error:
        msg += " with " + str(error) + " errors"
    print()
    print(msg)
    process_manager.shutdown()
