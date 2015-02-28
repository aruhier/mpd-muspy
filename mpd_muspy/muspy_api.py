#!/usr/bin/python
# Author: Anthony Ruhier

import mpd
import json
import musicbrainzngs
import urllib.error
import urllib.request
from config import SERVER, PORT, MUSPY_ADDR, MUSPY_USERNAME, MUSPY_PASSWORD, \
                   MUSPY_ID
from . import _release_name, _version

musicbrainzngs.set_useragent(_release_name, _version)


class ArtistNotFoundException(Exception):
    pass


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


class Muspy_api():
    #: URL to target the muspy api
    _muspy_api_url = MUSPY_ADDR

    #: custom opener with authentication
    _urlopener = None

    #: muspy username
    username = None

    #: muspy password
    password = None

    #: muspy user id
    user_id = None

    _mpdclient = None

    def __init__(self, username=MUSPY_USERNAME, password=MUSPY_PASSWORD,
                 user_id=MUSPY_ID, *args, **kwargs):
        self.username = username
        self.password = password
        self.user_id = user_id
        self._mpdclient = mpd.MPDClient()
        self._setup_auth_url()

    def _setup_auth_url(self):
        """
        Install a custom opener with authentication to muspy.

        Setup the HTTPPasswordMgrWithDefaultRealm to the MUSPY_API_URL
        """
        auth_handler = urllib.request.HTTPBasicAuthHandler()
        auth_handler.passwd = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        auth_handler.passwd.add_password(
            None, self._muspy_api_url, MUSPY_USERNAME, MUSPY_PASSWORD
        )
        self._urlopener = urllib.request.build_opener(auth_handler)

    def add_artist_mbid(self, mbid):
        """
        Add artist by its MusicBrainz id to the muspy account

        :param mbid: MusicBrainz id of the artist
        """
        request = urllib.request.Request(
            url=urllib.request.urljoin(
                self._muspy_api_url,
                "artists/" + self.user_id + "/" + str(mbid)),
        )
        request.get_method = lambda: 'PUT'
        try:
            self._urlopener.open(request)
        except urllib.error.HTTPError:
            raise ArtistNotFoundException("Artist not found")

    def add_artist(self, artist):
        """
        Add artist by its name to the muspy account

        :param artist: Artist name to add
        """
        return self.add_artist_mbid(get_mbid(artist, self._mpdclient))

    def get_artists(self):
        """
        Get artists followed by the user

        MuSpy returns a list of dicts of this form: [{
            'disambiguation':,
            'mbid': musicbrainz id,
            'name': artist name,
            'sort_name':,
        }, ...]
        :returns artists: list of dicts
        """
        artists = self._urlopener.open(self._muspy_api_url + "artists/" +
                                       self.user_id)
        return json.loads(artists.readall().decode())

    def get_urlopener(self):
        return self._urlopener
