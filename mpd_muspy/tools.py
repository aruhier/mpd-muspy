
import appdirs
from importlib.machinery import SourceFileLoader
import mpd
import musicbrainzngs
import os

from . import _release_name, _version
from .exceptions import ArtistNotFoundException


def get_config():
    return SourceFileLoader("config", get_config_path()).load_module()


def get_config_path():
    os.environ["XDG_CONFIG_DIRS"] = "/etc"
    CONFIG_DIRS = (
        appdirs.user_config_dir(_release_name),
        appdirs.site_config_dir(_release_name),
    )
    CONFIG_FILENAME = "config.py"

    for d in CONFIG_DIRS:
        config_path = os.path.join(d, CONFIG_FILENAME)
        if os.path.isfile(config_path):
            return config_path

    raise FileNotFoundError


config = get_config()
from config import SERVER, PORT
try:
    from config import USE_ALBUMARTIST
except:
    USE_ALBUMARTIST = False

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


def del_chars_from_string(s, chars_to_del):
    """
    Delete characters from list

    :param s: string to clean
    :param chars_to_del: characters to delete in string
    """
    if type(chars_to_del) != "str":
        for c in chars_to_del:
            s = s.replace(c, "")
    else:
        s = s.replace(chars_to_del, "")
    return s


def mpd_get_artists(mpdclient):
    """
    Get artists from MPD

    :param mpdclient: connection with MPD
    :type mpdclient: mpd.MPDClient()
    """
    mpdclient.connect(SERVER, PORT)
    tag_field = "albumartist" if USE_ALBUMARTIST else "artist"
    try:
        artists = set(str(artist).lower()
                      for artist in mpdclient.list(tag_field) if len(artist))
    except mpd.ConnectionError:
        mpdclient.connect(SERVER, PORT)
        artists = set(str(artist).lower()
                      for artist in mpdclient.list(tag_field) if len(artist))
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
    tag_field = "albumartist" if USE_ALBUMARTIST else "artist"
    try:
        artist_cs = mpdclient.search(tag_field, artist)[0]["artist"]
    except IndexError:
        raise ArtistNotFoundException("Artist is not in the mpd database")
    return mpdclient.list("album", tag_field, artist_cs)


def get_mbid(artist, mpdclient):
    """
    Get the musicbrainz id of an artist

    Search the artist id from the album we have in the mpd database to be
    almost sure the result is good.

    :param artist: artist name to get the id
    """
    ignore_chars = ["/", "\\", "!", "?"]
    LIMIT_NB_ARTIST = 15
    result = musicbrainzngs.search_artists(
        del_chars_from_string(artist, ignore_chars),
        LIMIT_NB_ARTIST)
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
                del_chars_from_string(album, ignore_chars),
                limit=LIMIT_NB_ALBUM)["release-list"]
            for i in result:
                artist_id = i["artist-credit"][0]["artist"]["id"]
                if artist_id in artists_prop:
                    return artist_id
        except:
            pass
    return artists_prop[0]
