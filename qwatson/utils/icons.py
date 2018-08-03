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
from PyQt5.QtWidgets import QApplication, QStyle

from qwatson import __rootdir__

dirname = os.path.join(__rootdir__, 'ressources', 'icons_png')
ICON_NAMES = {'master': 'qwatson',
              'process_start': 'process_start',
              'process_stop': 'process_stop',
              'process_cancel': 'process_cancel',
              'plus': 'plus_sign',
              'minus': 'minus_sign',
              'clear': 'clear-search',
              'edit': 'edit',
              'note': 'note',
              'erase-left': 'erase_left',
              'erase-right': 'erase_right',
              'home': 'home',
              'go-next': 'go-next',
              'go-previous': 'go-previous',
              'info': 'info',
              'insert_above': 'insert_row_above',
              'insert_below': 'insert_row_below'}

ICON_SIZES = {'huge': (128, 128),
              'Large': (64, 64),
              'large': (32, 32),
              'normal': (28, 28),
              'small': (20, 20),
              'tiny': (12, 12)}


def get_icon(name):
    return QIcon(os.path.join(dirname, ICON_NAMES[name]))


def get_iconsize(size):
    return QSize(*ICON_SIZES[size])


def get_standard_icon(constant):
    """
    Return a QIcon of a standard pixmap.

    See the link below for a list of valid constants:
    https://srinikom.github.io/pyside-docs/PySide/QtGui/QStyle.html
    """
    constant = getattr(QStyle, constant)
    style = QApplication.instance().style()
    return style.standardIcon(constant)


def get_standard_iconsize(constant):
    """
    Return the standard size of various component of the gui.

    https://srinikom.github.io/pyside-docs/PySide/QtGui/QStyle
    """
    style = QApplication.instance().style()
    if constant == 'messagebox':
        return style.pixelMetric(QStyle.PM_MessageBoxIconSize)
    elif constant == 'small':
        return style.pixelMetric(QStyle.PM_SmallIconSize)
