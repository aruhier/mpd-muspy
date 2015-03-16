#!/usr/bin/python
# Author: Anthony Ruhier

import multiprocessing
from .muspy_api import Muspy_api
from .tools import chunks, get_mbid, mpd_get_artists

# After multiple tests, it appears that this value is the best compromise to
# avoid HTTP error 400 with the musicbrainz api
NB_MULTIPROCESS = 3


def process_task(lst_without_mbid, artists_nb, artist_db, lock, counter,
                 muspy_artists, mpdclient):
    """
    Function launched by each process

    Add artists on muspy and marks it in the artists database.
    Tries to get the mbid from the list muspy_artists, because it is very fast.
    If it cannot find it, search on musicbrainz.

    :param lst_without_mbid: list of artists, splited for each process, that
        don't have a musicbrainz id
    :type artists: list
    :param artists_nb: total artists to upload. Different of
        len(lst_without_mbid), here it is the total number of artists of all
        processes
    :type artists_nb: int
    :param artist_db: database of artists, in the shared memory
    :type artist_db: SyncManager.Artist_db()
    :param lock: lock shared between the processes
    :type lock: multiprocessing.Lock
    :param counter: integer in the shared memory
    :type counter: multiprocessing.Value("i")
    :param muspy_artists: list of artists already on the muspy account
    :type muspy_artists: list of dict
    :param mpdclient:
    """
    for artist in lst_without_mbid:
        error = ""
        try:
            mbid = None
            for ma in muspy_artists:
                if ma["name"] == artist:
                    mbid = ma["mbid"]
                    break
            if mbid is None:
                mbid = get_mbid(artist, mpdclient)
            if mbid is not None:
                with lock:
                    artist_db.set_mbid(artist, mbid)
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


def fetch_missing_mbid(artist_db, muspy_artists, mpdclient):
    """
    Initialize the synchronization in several process

    :param artist_db: Artist_db() object in the shared memory
    :type artist_db: SyncManager.Artist_db
    :param muspy_artists: artists already on the muspy account
    :type muspy_artists: list of dict
    :param mpdclient: client for mpd
    :type mpdclient: SyncManager.MPDClient
    """
    # Get all artists name that don't have an musicbrainz id
    lst_without_mbid = [a["name"]
                        for a in artist_db.get_artists(fields=("mbid",))
                        if not ("mbid" in a.keys() and a["mbid"] is not None)]

    manager = multiprocessing.Manager()
    lock = manager.Lock()
    counter = manager.Value("i", 0)
    artists_nb = len(lst_without_mbid)
    artists_nb_by_split = int(artists_nb / NB_MULTIPROCESS)
    pool = multiprocessing.Pool()

    for l in chunks(lst_without_mbid, artists_nb_by_split):
        pool.apply_async(
            process_task,
            kwds={"lst_without_mbid": l,
                  "artists_nb": artists_nb, "artist_db": artist_db,
                  "lock": lock, "counter": counter,
                  "muspy_artists": muspy_artists, "mpdclient": mpdclient}
        )
    pool.close()
    pool.join()


def update_artists_from_muspy(artist_db, muspy_artists):
    """
    Update the uploaded state of artists from the ones already on the muspy
    account.

    :param artist_db: database of local artists
    :param muspy_artists: list of artists already on the muspy account
    """
    local_artists = artist_db.get_artists(fields=("mbid", "uploaded",))
    muspy_mbid_list = [ma["mbid"] for ma in muspy_artists]
    for la in local_artists:
        try:
            if la["mbid"] in muspy_mbid_list and la["uploaded"] is False:
                artist_db.mark_as_uploaded(la["name"])
            elif la["mbid"] not in muspy_mbid_list and la["uploaded"] is True:
                artist_db.mark_as_non_uploaded(la["name"])
        except KeyError:
            pass
    artist_db.save()


def presync(artist_db, mpdclient):
    print("Get mpd artists...")
    artists = mpd_get_artists(mpdclient)
    artists_added, artists_removed = artist_db.merge(artists)

    mapi = Muspy_api()
    muspy_artists = mapi.get_artists()

    print("Fetch the missing musicbrainz ids...")
    fetch_missing_mbid(artist_db, muspy_artists, mpdclient)
    print("Done\n")

    # Update the uploaded status of artists in the db with the muspy account
    print("Pre-synchronization with muspy...")
    update_artists_from_muspy(artist_db, muspy_artists)
    artist_db.save()

    non_uploaded_artists = artist_db.get_artists(fields=("mbid",),
                                                 uploaded=False)
    print()
    print(len(non_uploaded_artists), "artist(s) non uploaded on muspy")
    print(len(artists_added), "artist(s) added")
    print(len(artists_removed), "artist(s) removed")

    return non_uploaded_artists
