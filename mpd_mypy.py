#!/usr/bin/python

import json
import mpd
import os

SERVER = "localhost"
PORT = 6600
ARTISTS_JSON = "artists.json"


class Artist_db():
    def __init__(self, artists={}, jsonpath=None):
        self.artists = artists
        self.jsonpath = jsonpath
        if jsonpath is not None:
            try:
                self.load()
            except:
                pass

    def _diff_artists(self, artists):
        """
        Compare keys of self.artists with artists

        :param artists: list of artists to compare with
        :type artists: list
        :returns keys: list of artists differents between self.artists and
            artists
        """
        db_keys = set(self.artists.keys())
        set_artists = set(artists)
        return db_keys.difference(set_artists).symmetric_difference(
            set_artists.difference(db_keys))

    def load(self):
        """
        Refresh the artists list from the json file
        """
        with open(self.jsonpath, "r+") as f:
            self.artists = json.load(f)

    def save(self):
        """
        Save the artists list into the json file
        """
        new_db = not os.path.exists(self.jsonpath)
        fmode = "a+" if new_db else "r+"
        try:
            with open(self.jsonpath, fmode) as f:
                json.dump(self.artists, f, indent=4)
        except Exception as e:
            print("Error when saving the database")
            print(e)

    def add(self, artists):
        """
        Add artist(s) in the db

        :param artist: artist(s) to add into the db
        :type artists: str or list
        """
        if type(artists) is not str:
            try:
                for a in artists:
                    self.add(a)
                return
            except:
                pass

        if artists not in self.artists.keys():
            self.artists[str(artists)] = {"uploaded": False, }

    def remove(self, artists):
        """
        Remove artist off the db

        :param artist: artist(s) to remove off the db
        :type artists: str or list
        """
        if type(artists) is not str:
            try:
                for a in artists:
                    self.remove(a)
                return
            except:
                pass

        if artists in self.artists.keys:
            self.artists.pop(artists)

    def merge(self, artists):
        """
        Merge artists in the db with a list of artists name sent in parameter

        :param artists: list of artists to compare the db with
        :type artists: list
        :returns nb_off_diff: number of artists removed or added
        :rtype: int
        """
        a_diff = self._diff_artists(artists)
        for a in a_diff:
            if a in self.artists:
                self.remove(a)
            else:
                self.add(a)
        return len(a_diff)


def connect(mpdclient):
    """
    Handle connection to the mpd server
    """
    mpdclient.connect(SERVER, PORT)


artist_db = Artist_db(jsonpath=ARTISTS_JSON)
mpdclient = mpd.MPDClient()
connect(mpdclient)
try:
    artists = set(str(artist).lower() for artist in mpdclient.list("artist")
                  if artist != "")
except mpd.ConnectionError:
    connect(mpdclient)
    artists = set(str(artist).lower() for artist in mpdclient.list("artist")
                  if artist != "")
print(artist_db.merge(artists), "artist(s) updated")
artist_db.save()
