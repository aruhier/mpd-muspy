#!/usr/bin/python
# Author: Anthony Ruhier

import urllib
from config import MUSPY_USERNAME, MUSPY_PASSWORD


class muspy_api():
    #: URL to target the muspy api
    _muspy_api_url = "https://muspy.com/api/1/"

    def setup_auth_url(self, username=MUSPY_USERNAME, password=MUSPY_PASSWORD):
        """
        Install a custom opener with authentication to muspy.

        Setup the HTTPPasswordMgrWithDefaultRealm to the MUSPY_API_URL

        :param username: muspy username
        :type username: str
        :param password: muspy password
        """
        auth_handler = urllib.request.HTTPBasicAuthHandler()
        auth_handler.passwd = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        auth_handler.passwd.add_password(
            None, self._muspy_api_url, MUSPY_USERNAME, MUSPY_PASSWORD
        )
        opener = urllib.request.build_opener(auth_handler)
        urllib.request.install_opener(opener)
