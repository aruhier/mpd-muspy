#!/usr/bin/python
# Author: Anthony Ruhier

import json
import os


class Artist_db():
    def __init__(self, artists={}, jsonpath=None):
        self.artists = artists
        self.jsonpath = jsonpath
        if jsonpath is not None:
            try:
                self.load()
            except FileNotFoundError:
                pass
            except Exception as e:
                print(e)
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
        with open(self.jsonpath, "r") as f:
            self.artists = json.load(f)

    def save(self):
        """
        Save the artists list into the json file
        """
        new_db = not os.path.exists(self.jsonpath)
        fmode = "a" if new_db else "w"
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

    def get_non_uploaded(self):
        """
        Get the list of the non uploaded (on muspy) artists.

        :returns artists
        """
        return [artist for artist, val in self.artists.items()
                if self.artists[artist]["uploaded"] is False]

    def mark_as_uploaded(self, artist):
        """
        Mark an artist as uploaded
        """
        self.artists[artist]["uploaded"] = True

    def merge(self, artists):
        """
        Merge artists in the db with a list of artists name sent in parameter

        :param artists: list of artists to compare the db with
        :type artists: list
        :returns (added, deleted): tuple of removed and added artists list
        :rtype: tuple
        """
        a_diff = self._diff_artists(artists)
        added = []
        removed = []
        for a in a_diff:
            if a in self.artists:
                self.remove(a)
                removed.append(a)
            else:
                self.add(a)
                added.append(a)
        return (added, removed)
