"""Run-time settings shared by the generator modules. sync.py fills these in before importing them."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PRE_IMPORT = os.path.join(HERE, '..', 'data', 'pre_import_wiki.json')

VERSION = '2.14'          # as shown on the docs front page, e.g. "2.15"
VERSION_FULL = '2.14.0'   # used in {{Changelog|Key|x.y.z}}

LIVE_OTHER_TITLES = set()  # titles on the live wiki that this tool did not create
CHANGELOG_DATA = None      # live text of Module:Changelog/data (None = use the pre-import copy)

CLASS_PAGES = False        # class pages are built from the game files, not the docs, so they are left alone
