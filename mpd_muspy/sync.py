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


def process_task(artists, artist_db, muspy_api, lock):
    for artist in artists:
        try:
            muspy_api.add_artist(artist)
            lock.acquire()
            artist_db.mark_as_uploaded(artist)
            artist_db.save()
            lock.release()
            print("Artist:", artist, ". Done...")
        except Exception as e:
            print(e)
            pass


def start_process(non_uploaded_artists, artist_db):
    process_list = []
    lock = multiprocessing.Lock()
    process_list = []
    muspy_api = Muspy_api()
    nb_artists_by_split = int(len(non_uploaded_artists) / NB_MULTIPROCESS)
    for l in chunks(non_uploaded_artists, nb_artists_by_split):
        process = multiprocessing.Process(
            target=process_task,
            kwargs={"artists": l, "artist_db": artist_db,
                    "muspy_api": muspy_api, "lock": lock}
        )
        process.daemon = True
        process.start()
        process_list.append(process)

    for process in process_list:
        process.join()


def run():
    process_manager = SyncManager()
    process_manager.start()
    artist_db = process_manager.Artist_db(jsonpath=ARTISTS_JSON)
    mpdclient = mpd.MPDClient()

    artists = mpd_get_artists(artist_db, mpdclient)
    artists_removed, artists_added = artist_db.merge(artists)
    artist_db.save()
    non_uploaded_artists = artist_db.get_non_uploaded()
    artists = None

    print(len(non_uploaded_artists), "artist(s) non uploaded on muspy")
    print(len(artists_added), "artist(s) added")
    print(len(artists_removed), "artist(s) removed")

    start_process(non_uploaded_artists, artist_db)
    print("Done: ",
          len(non_uploaded_artists) - len(artist_db.get_non_uploaded()),
          "artist(s) updated")
