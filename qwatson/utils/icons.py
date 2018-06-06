# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Imports: standard libraries

import os

# ---- Imports: third parties

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon

from qwatson import __rootdir__

dirname = os.path.join(__rootdir__, 'ressources', 'icons_png')
ICON_NAMES = {'master': 'master',
              'process_start': 'process_start',
              'process_stop': 'process_stop',
              'plus': 'plus_sign',
              'minus': 'minus_sign',
              'clear': 'clear-search',
              'edit': 'edit',
              'note': 'note',
              'erase-left': 'erase_left',
              'erase-right': 'erase_right',
              'home': 'home',
              'go-next': 'go-next',
              'go-previous': 'go-previous'}

ICON_SIZES = {'large': (32, 32),
              'normal': (28, 28),
              'small': (20, 20)}


def get_icon(name):
    return QIcon(os.path.join(dirname, ICON_NAMES[name]))


def get_iconsize(size):
    return QSize(*ICON_SIZES[size])
