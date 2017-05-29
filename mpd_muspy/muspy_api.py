#!/usr/bin/python
# Author: Anthony Ruhier

import urllib.request
import mpd
import requests
import config
from .exceptions import ArtistNotFoundException
from .tools import get_mbid, get_config

config = get_config()
from config import MUSPY_ADDR, MUSPY_USERNAME, MUSPY_PASSWORD, MUSPY_ID


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
        try:
            self._ssl_verify = not config.MUSPY_FORCE_SSL_ACCEPT
            if not self._ssl_verify:
                requests.packages.urllib3.disable_warnings()
        except:
            self._ssl_verify = True

    def add_artist_mbid(self, mbid):
        """
        Add artist by its MusicBrainz id to the muspy account

        :param mbid: MusicBrainz id of the artist
        """
        try:
            requests.put(
                urllib.request.urljoin(
                    self._muspy_api_url,
                    "artists/" + self.user_id + "/" + str(mbid)
                ),
                auth=(MUSPY_USERNAME, MUSPY_PASSWORD),
                verify=self._ssl_verify,
            )
        except requests.HTTPError:
            raise ArtistNotFoundException("Artist not found")

    def del_artist_mbid(self, mbid):
        """
        Delete artist by its MusicBrainz id of the muspy account

        :param mbid: MusicBrainz id of the artist
        """
        try:
            requests.delete(
                urllib.request.urljoin(
                    self._muspy_api_url,
                    "artists/" + self.user_id + "/" + str(mbid)
                ),
                auth=(MUSPY_USERNAME, MUSPY_PASSWORD),
                verify=self._ssl_verify,
            )
        except requests.HTTPError:
            raise ArtistNotFoundException(
                "Artist is not indexed in the Muspy account"
            )

    def add_artist(self, artist):
        """
        Add artist by its name to the muspy account

        :param artist: Artist name to add
        """
        return self.add_artist_mbid(get_mbid(artist, self._mpdclient))

    def del_artist(self, artist):
        """
        Delete artist by its name from the muspy account

        :param artist: Artist name to add
        """
        return self.del_artist_mbid(get_mbid(artist, self._mpdclient))

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
        r = requests.get(
            urllib.request.urljoin(
                self._muspy_api_url,
                "artists/" + self.user_id
            ),
            auth=(MUSPY_USERNAME, MUSPY_PASSWORD),
            verify=self._ssl_verify,
        )
        return [{"name": a["name"].lower(), "mbid": a["mbid"]}
                for a in r.json()]
