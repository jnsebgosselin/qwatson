# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys
import os
import os.path as osp

# ---- Third party imports

import pytest
from PyQt5.QtCore import Qt

# ---- Local imports

from qwatson.mainwindow import QWatson


# ---- Qt Test Fixtures

WORKDIR = osp.dirname(__file__)


@pytest.fixture
def qwatson_bot(qtbot):
    qwatson = QWatson(WORKDIR)
    qtbot.addWidget(qwatson)

    return qwatson, qtbot


# Test MainWindow
# -------------------------------

@pytest.mark.run(order=11)
def test_mainwindow_init(qwatson_bot):
    """
    Tests that the QWatson main widget starts correctly.
    """
    qwatson, qtbot = qwatson_bot
    assert qwatson
    assert qwatson.client.frames_file == osp.join(WORKDIR, 'frames')


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
#     pytest.main()
