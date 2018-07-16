# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import os

# ---- Third party imports

import pytest

# ---- Local imports

from qwatson.utils.colors import get_qcolor, set_widget_palette
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QLabel


def test_get_qcolor(qtbot):
    """
    Test that the various available methods to create a QColor are working
    as expected.
    """
    qcolor = QColor('red')
    assert get_qcolor(QColor('red')) == qcolor
    assert get_qcolor('red') == qcolor
    assert get_qcolor((255, 0, 0)) == qcolor
    assert get_qcolor('#FF0000') == qcolor
    assert get_qcolor('window') == QPalette().window().color()
    with pytest.raises(ValueError):
        get_qcolor('dummy')


def test_set_widget_palette(qtbot):
    """
    Asser that setting the background and foreground colors for widgets works
    as expected.
    """
    qlabel = QLabel('Coucou')
    qlabel.setAutoFillBackground(True)

    set_widget_palette(qlabel, bgcolor='black', fgcolor='red')
    assert qlabel.palette().color(qlabel.backgroundRole()) == QColor('black')
    assert qlabel.palette().color(qlabel.foregroundRole()) == QColor('red')


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
