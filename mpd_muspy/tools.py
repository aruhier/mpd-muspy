#!/usr/bin/python
# Author: Anthony Ruhier

import mpd
import musicbrainzngs
from . import _release_name, _version
from config import SERVER, PORT
from .exceptions import ArtistNotFoundException


musicbrainzngs.set_useragent(_release_name, _version)


def chunks(l, n):
    """
    Yield successive n-sized chunks from l.

    :param l: list to split
    :param n: number of elements wanted in each list split
    """
    n = 1 if n <= 0 else n
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


def get_mpd_albums(artist, mpdclient):
    """
    Get list of albums in the mpd database for an artist

    :param artist: artist name to filter
    :param mpdclient: connector with the mpd server
    :type mpdclient: mpd.MPDClient()
    """
    try:
        mpdclient.status()
    except mpd.ConnectionError:
        mpdclient.connect(SERVER, PORT)
    # The mpd module is using case sensitive filters in list(). Artist has to
    # be spelled correctly
    try:
        artist_cs = mpdclient.search("artist", artist)[0]["artist"]
    except IndexError:
        raise ArtistNotFoundException("Artist is not in the mpd database")
    return mpdclient.list("album", "artist", artist_cs)


def get_mbid(artist, mpdclient):
    """
    Get the musicbrainz id of an artist

    Search the artist id from the album we have in the mpd database to be
    almost sure the result is good.

    :param artist: artist name to get the id
    """
    LIMIT_NB_ARTIST = 15
    result = musicbrainzngs.search_artists(artist, LIMIT_NB_ARTIST)
    if result["artist-count"] == 0:
        raise ArtistNotFoundException("Artist not found")
    artists_prop = [a["id"] for a in result["artist-list"]]
    if result["artist-count"] == 1:
        return artists_prop[0]

    # Tries to get the artist id of one of our album of this artist
    albums = get_mpd_albums(artist, mpdclient)
    # We don't want to test all choices returned by musicbrainz for an album,
    # so we will keep only the LIMIT_NB_ALBUM'th first ones.
    LIMIT_NB_ALBUM = 10
    for album in albums:
        try:
            result = musicbrainzngs.search_releases(
                album, limit=LIMIT_NB_ALBUM)["release-list"]
            for i in result:
                artist_id = i["artist-credit"][0]["artist"]["id"]
                if artist_id in artists_prop:
                    return artist_id
        except:
            pass
    return artists_prop[0]
