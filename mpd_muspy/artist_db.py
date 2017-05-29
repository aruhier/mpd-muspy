
import appdirs
import json
import os
from . import _current_dir
from .tools import get_config

config = get_config()


class Artist_db():
    def __init__(self, jsonpath=None, artists=None):
        self._artists = artists if artists is not None else dict()
        self.ignore_list = config.IGNORE_LIST or tuple()
        self.jsonpath = jsonpath
        if jsonpath is not None:
            try:
                if artists is None:
                    self.load()
            except FileNotFoundError:
                pass
            except:
                print("Error when importing the database, creating a fresh "
                      "one...")
                pass

    def _diff_artists(self, artists):
        """
        Compare keys of self._artists with artists

        :param artists: list of artists to compare with
        :type artists: list
        :returns keys: list of artists differents between self._artists and
            artists
        """
        try:
            db_keys = set(self._artists.keys())
        except:
            db_keys = set()
        set_artists = set(artists)
        return db_keys.difference(set_artists).symmetric_difference(
            set_artists.difference(db_keys))

    def _get_fields(self):
        """
        Get the database fields/columns

        :returns fields
        """
        try:
            fields = list(next(iter(self._artists.values())).keys())
        except StopIteration:
            fields = []
        return fields

    def load(self):
        """
        Refresh the artists list from the json file
        """
        with open(self.jsonpath, "r") as f:
            self._artists = json.load(f)

    def save(self):
        """
        Save the artists list into the json file
        """
        new_db = not os.path.exists(self.jsonpath)
        fmode = "a" if new_db else "w"
        try:
            artist_db_dirname = os.path.dirname(self.jsonpath)
            if not os.path.exists(artist_db_dirname):
                os.makedirs(artist_db_dirname)
            with open(self.jsonpath, fmode) as f:
                json.dump(self._artists, f, indent=4)
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

        if artists not in self._artists.keys():
            self._artists[str(artists)] = {"uploaded": False, }

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

        if artists in self._artists.keys():
            self._artists.pop(artists)

    def _artists_grouped_by(self, artists, group_by, fields=None):
        """
        Return artists grouped by a field. The get_artists function would
        already have done the filters

        :param artists: artists to group by
        :type artists: dict
        :param group_by: field use to grouping
        :param fields: get other fields, like musicbrainz id. By default, will
                       just the names will be returned
        """
        artists_grouped = dict()
        for artist, val in artists.items():
            if fields is None:
                artist_insert = artist
            else:
                artist_insert = {field: self._artists[artist][field]
                                 for field in fields if field in
                                 self._artists[artist].keys()}
                artist_insert["name"] = artist

            if val[group_by] in artists_grouped.keys():
                artists_grouped[val[group_by]].append(artist_insert)
            else:
                artists_grouped[val[group_by]] = [artist_insert, ]
        return artists_grouped

    def get_artists(self, fields=None, uploaded=None, group_by=None):
        """
        Get the list of artists name, with optional filter and group by.

        If fields is None, it will return a list of artist names. Otherwise, it
        will return a list of dict, with the select fields as keys, and the
        artist name with the key "name". If the field does not exist for an
        artist, it will not ignored (for this artist).
        If group_by is not None, will return a list of artist names group by
        the wanted field.

        :param fields: fields to select
        :type fields: tuple
        :param uploaded: filter on the uploaded field
        :type uploaded: bool
        :param group_by: group by a field
        :type group_by: str
        :returns artists
        """
        artists = self._artists

        for ignore_artist in self.ignore_list:
            try:
                artists.pop(ignore_artist)
            except KeyError:
                continue

        if uploaded is not None:
            artists = {artist: val for artist, val in self._artists.items()
                       if val["uploaded"] == uploaded}

        if group_by is not None and group_by in self._get_fields():
            return self._artists_grouped_by(artists, group_by, fields)

        if fields is None:
            artist_list = [artist for artist in artists.keys()]
        else:
            artist_list = []
            for artist in artists:
                artist_insert = {field: self._artists[artist][field]
                                 for field in fields if field in
                                 self._artists[artist].keys()}
                artist_insert["name"] = artist
                artist_list.append(artist_insert)

        return artist_list

    def get_mbid(self, artist):
        """
        Get the musicbrainz id of an artist

        :param artist: artist name
        """
        try:
            mbid = self._artists[artist]["mbid"]
        except KeyError:
            mbid = None
        return mbid

    def is_ignored(self, artist):
        """
        Check if artist is ignored or not

        :param artist: artist name
        """
        return artist.lower() in self.ignore_list

    def mark_as_uploaded(self, artist):
        """
        Mark an artist as uploaded
        """
        self._artists[artist]["uploaded"] = True

    def mark_as_non_uploaded(self, artist):
        """
        Mark an artist as non uploaded
        """
        self._artists[artist]["uploaded"] = False

    def set_mbid(self, artist, mbid):
        """
        Update the musicbrainz id of an artist

        :param artist: artist name
        :param mbid: Musicbrainz id
        """
        self._artists[artist]["mbid"] = mbid

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
            if a in self.ignore_list:
                continue
            elif a in self._artists:
                self.remove(a)
                removed.append(a)
            else:
                self.add(a)
                added.append(a)
        return (added, removed)
