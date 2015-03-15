#!/usr/bin/python
# Author: Anthony Ruhier

import mpd
import json
import urllib.error
import urllib.request
from config import MUSPY_ADDR, MUSPY_USERNAME, MUSPY_PASSWORD, MUSPY_ID
from .exceptions import ArtistNotFoundException
from .tools import get_mbid


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

    #: MPDClient object
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
        return [{"name": a["name"].lower(), "mbid": a["mbid"]}
                for a in json.loads(artists.readall().decode())]
