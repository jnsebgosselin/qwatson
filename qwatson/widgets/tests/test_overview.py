# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import os
import os.path as osp

# ---- Third party imports

import pytest
from PyQt5.QtCore import Qt

# ---- Local imports

from qwatson.mainwindow import QWatson
from qwatson.utils.dates import local_arrow_from_tuple


APPDIR = osp.join(osp.dirname(__file__), 'appdir')
FRAME_FILE = osp.join(APPDIR, 'frames')

NOW = local_arrow_from_tuple((2018, 6, 14, 23, 59, 0))
SPAN = NOW.floor('week').span('week')


# ---- Fixtures and utilities

@pytest.fixture
def overview_creator(qtbot, mocker):
    if not osp.exists(FRAME_FILE):
        create_framefile(mocker)

    mocker.patch('arrow.now', return_value=NOW)

    qwatson = QWatson(config_dir=APPDIR)
    overview = qwatson.overview_widg
    qtbot.addWidget(overview)
    return overview, qtbot, mocker


def create_framefile(mocker):
    """
    Create a framefile that span over the current week with one activity
    every hour.
    """
    qwatson = QWatson(APPDIR)

    i = 0
    while True:
        start = SPAN[0].shift(hours=i*6)
        mocker.patch('arrow.now', return_value=start)
        qwatson.client.start('test_overview')
        i += 1
        stop = SPAN[0].shift(hours=i*6)
        mocker.patch('arrow.now', return_value=stop)
        qwatson.stop_watson(
            message='activity #%s' % i, project='test_overview', tags=None,
            round_to=5)

        if stop >= SPAN[1]:
            break
    qwatson.client.save()


def test_overview_init(overview_creator):
    """Test that the overview is initialized correctly."""
    overview, qtbot, mocker = overview_creator
    overview.show()
    qtbot.waitForWindowShown(overview)

    assert overview.isVisible()

    assert overview.table_widg.total_seconds == 7*24*1*60*60
    assert len(overview.table_widg.tables) == 7
    assert overview.table_widg.last_focused_table is None
    assert overview.table_widg.date_span == SPAN


def test_overview_row_selection(overview_creator):
    """
    Test that table and row selection is working as expected.
    """
    overview, qtbot, mocker = overview_creator
    overview.show()
    qtbot.waitForWindowShown(overview)

    tables = overview.table_widg.tables

    # Mouse click on the second row of the second table.

    index = tables[1].view.proxy_model.index(1, 0)
    visual_rect = tables[1].view.visualRect(index)

    qtbot.mouseClick(
        tables[1].view.viewport(), Qt.LeftButton, pos=visual_rect.center())

    assert overview.table_widg.last_focused_table == tables[1]
    assert overview.table_widg.last_focused_table.get_selected_row() == 1

    # Mouse click on the third row of the second table.

    index = tables[2].view.proxy_model.index(2, 0)
    visual_rect = tables[2].view.visualRect(index)

    qtbot.mouseClick(
        tables[2].view.viewport(), Qt.LeftButton, pos=visual_rect.center())

    assert overview.table_widg.last_focused_table == tables[2]
    assert tables[2].get_selected_row() == 2

    # Assert that all tables but 2 have no selected row

    for table in tables:
        if table != overview.table_widg.last_focused_table:
            assert table.get_selected_row() is None


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
