#!/usr/bin/python
# Author: Anthony Ruhier

import json
import musicbrainzngs
import urllib.error
import urllib.request
from config import MUSPY_USERNAME, MUSPY_PASSWORD, MUSPY_ID
from . import _release_name, _version


class ArtistNotFoundException(Exception):
    pass


def get_mbid(artist):
    """
    Get the musicbrainz id of an artist
    """
    musicbrainzngs.set_useragent(_release_name, _version)
    result = musicbrainzngs.search_artists(artist)
    try:
        artist_mbid = result["artist-list"][0]["id"]
    except (KeyError, IndexError):
        raise ArtistNotFoundException("Artist not found")
    return artist_mbid


class Muspy_api():
    #: URL to target the muspy api
    _muspy_api_url = "https://muspy.com/api/1/"

    #: custom opener with authentication
    _urlopener = None

    #: muspy username
    username = None

    #: muspy password
    password = None

    #: muspy user id
    user_id = None

    def __init__(self, username=MUSPY_USERNAME, password=MUSPY_PASSWORD,
                 user_id=MUSPY_ID, *args, **kwargs):
        self.username = username
        self.password = password
        self.user_id = user_id
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
        http_handler = urllib.request.HTTPHandler()
        self._urlopener = urllib.request.build_opener(
            auth_handler,
            http_handler)

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
        return self.add_artist_mbid(get_mbid(artist))

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
