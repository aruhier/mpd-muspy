#!/usr/bin/python
# Author: Anthony Ruhier

import json
import urllib.request
from config import MUSPY_USERNAME, MUSPY_PASSWORD, MUSPY_ID


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
        self._urlopener = urllib.request.build_opener(auth_handler)

    def add_artist(self, mbid):
        """
        Add artist to the muspy account

        :param mbid: MusicBrainz id of the artist to add
        """

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
