# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.


# ---- Imports: third parties

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QStyleOption


def get_qcolor(*args):
    """
    Return a QColor either from a RGB tuple of int, a RGB Hex Code,
    a supported Qt color name, or a QPalette color group.

    https://srinikom.github.io/pyside-docs/PySide/QtGui/QPalette.html
    https://srinikom.github.io/pyside-docs/PySide/QtGui/QColor.html
    """
    if isinstance(args[0], QColor):
        return args[0]

    if isinstance(args[0], tuple):
        return QColor(*args[0])

    if isinstance(args[0], str):
        if args[0].startswith('#') or args[0] in QColor.colorNames():
            return QColor(args[0])

        try:
            return getattr(QStyleOption().palette, args[0])().color()
        except AttributeError:
            pass

    raise ValueError("The provided color argument is not valid")


def set_widget_palette(widget, bgcolor=None, fgcolor=None):
    """Set the background and foreground color of the widget."""
    p = widget.palette()
    if bgcolor is not None:
        p.setColor(widget.backgroundRole(), get_qcolor(bgcolor))
    if fgcolor is not None:
        p.setColor(widget.foregroundRole(), get_qcolor(fgcolor))
    widget.setPalette(p)
