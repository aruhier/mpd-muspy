#!/usr/bin/env python3

"""
Sync artists of your MPD database with your MuSpy account.
See:
    https://github.com/Anthony25/mpd-muspy
"""

from setuptools import setup

setup(
    name="mpd-muspy",
    version="1.0.1",

    description="Sync artists of your MPD database with your MuSpy account",

    url="https://github.com/Anthony25/mpd-muspy",
    author="Anthony25 <Anthony Ruhier>",
    author_email="anthony.ruhier@gmail.com",

    license="Simplified BSD",

    classifiers=[
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: BSD License",
    ],

    keywords="mpd",
    packages=["mpd_muspy", ],
    install_requires=[
        "appdirs", "argparse", "python-mpd2", "musicbrainzngs", "requests",
        "urllib3"
    ],
    entry_points={
        'console_scripts': [
            'mpd-muspy = mpd_muspy.__main__:parse_args',
        ],
    }
)
