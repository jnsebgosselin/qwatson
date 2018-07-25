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
from qwatson.utils.fileio import delete_file_safely
from qwatson.utils.dates import qdatetime_from_str
from qwatson.models.delegates import DateTimeDelegate


APPDIR = osp.join(osp.dirname(__file__), 'appdir')
FRAME_FILE = osp.join(APPDIR, 'frames')

NOW = local_arrow_from_tuple((2018, 6, 17, 23, 59, 0))
SPAN = NOW.floor('week').span('week')
delete_file_safely(FRAME_FILE)


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
    Create a framefile that span over the current week with 2 activity of
    6 hours per day, between 6:00 AM and 12:00 PM and 6:00PM and 12:00AM.
    """
    qwatson = QWatson(APPDIR)

    i = 1
    while True:
        start = SPAN[0].shift(hours=i*6)
        mocker.patch('arrow.now', return_value=start)
        qwatson.client.start('test_overview')

        stop = SPAN[0].shift(hours=(i+1)*6)
        stop = SPAN[0].shift(hours=(i+1)*6)
        mocker.patch('arrow.now', return_value=stop)
        qwatson.stop_watson(
            message='activity #%s' % i, project='test_overview', tags=None,
            round_to=5)

        if stop >= SPAN[1]:
            break
        i += 2

    qwatson.client.save()


def test_overview_init(overview_creator):
    """Test that the overview is initialized correctly."""
    overview, qtbot, mocker = overview_creator
    overview.show()
    qtbot.waitForWindowShown(overview)

    assert overview.isVisible()

    assert overview.table_widg.total_seconds == 7*(2*6)*60*60
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

    # Assert that all but one table have a row and a frame selected.
    assert overview.table_widg.last_focused_table == tables[1]
    for table in tables:
        if table != overview.table_widg.last_focused_table:
            assert table.get_selected_row() is None
            assert table.get_selected_frame_index() is None
        else:
            assert table.get_selected_row() == 1
            assert table.get_selected_frame_index() == 2 + 2 - 1

    # Mouse click on the first row of the second table.

    index = tables[2].view.proxy_model.index(2, 0)
    visual_rect = tables[2].view.visualRect(index)

    qtbot.mouseClick(
        tables[2].view.viewport(), Qt.LeftButton, pos=visual_rect.center())

    assert overview.table_widg.last_focused_table == tables[2]

    # Assert that all tables but 2 have no selected row and frame.

    for table in tables:
        if table != overview.table_widg.last_focused_table:
            assert table.get_selected_row() is None
            assert table.get_selected_frame_index() is None
        else:
            assert table.get_selected_row() == 0
            assert table.get_selected_frame_index() == 2 + 2 + 1 - 1


def test_mouse_hovered_row(overview_creator):
    """
    Test that the highlighting of mouse hovered row is working as expected.
    """
    overview, qtbot, mocker = overview_creator
    overview.show()
    qtbot.waitForWindowShown(overview)

    tables = overview.table_widg.tables

    # Mouse hover the second row of the second table.

    index = tables[1].view.proxy_model.index(1, 0)
    visual_rect = tables[1].view.visualRect(index)

    qtbot.mouseMove(tables[1].view.viewport(), pos=visual_rect.center())
    tables[1].view.itemEnterEvent(index)
    assert tables[1].view._hovered_row == 1

    # Mouse hover the first row of the fourth table and simulate a change of
    # value of the scrollbar. Assert that the _hovered_row of the second
    # table is now None and that the  _hovered_row of the fourth table is 0.

    index = tables[4].view.proxy_model.index(0, 0)
    visual_rect = tables[4].view.visualRect(index)

    qtbot.mouseMove(tables[4].view.viewport(), pos=visual_rect.center())
    overview.table_widg.srollbar_value_changed(
        overview.table_widg.scrollarea.verticalScrollBar().value())

    assert tables[1].view._hovered_row is None
    assert tables[4].view._hovered_row == 0


# ---- Test Edits

def test_edit_start_datetime(overview_creator):
    """Test editing the start date in the activity overview table."""
    overview, qtbot, mocker = overview_creator
    overview.show()
    qtbot.waitForWindowShown(overview)

    # Edit the start date of the first frame in the first table.

    table = overview.table_widg.tables[0]
    index = table.view.proxy_model.index(0, 0)
    delegate = table.view.itemDelegate(index)
    assert isinstance(delegate, DateTimeDelegate)

    # Check that the start value is contraint by the stop value of the frame.

    table.view.edit(index)
    assert delegate.editor.isVisible()
    assert (delegate.editor.dateTime().toString("yyyy-MM-dd hh:mm") ==
            '2018-06-11 06:00')

    delegate.editor.setDateTime(qdatetime_from_str('2018-06-11 15:23'))
    with qtbot.waitSignal(table.view.proxy_model.sig_sourcemodel_changed):
        qtbot.keyPress(delegate.editor, Qt.Key_Enter)

    assert (overview.model.client.frames[0].start.format('YYYY-MM-DD HH:mm') ==
            '2018-06-11 12:00')

    # Check that the stat is changed correctly when a valid value is
    # provided.

    table.view.edit(index)
    assert delegate.editor.isVisible()
    assert (delegate.editor.dateTime().toString("yyyy-MM-dd hh:mm") ==
            '2018-06-11 12:00')

    delegate.editor.setDateTime(qdatetime_from_str('2018-06-11 07:16'))
    with qtbot.waitSignal(table.view.proxy_model.sig_sourcemodel_changed):
        qtbot.keyPress(delegate.editor, Qt.Key_Enter)

    assert (overview.model.client.frames[0].start.format('YYYY-MM-DD HH:mm') ==
            '2018-06-11 07:16')


def test_edit_stop_datetime(overview_creator):
    """Test editing the stop date in the activity overview table."""
    overview, qtbot, mocker = overview_creator
    overview.show()
    qtbot.waitForWindowShown(overview)

    # Edit the stop date of the first frame of the third table

    table = overview.table_widg.tables[2]
    index = table.view.proxy_model.index(0, 1)
    delegate = table.view.itemDelegate(table.view.proxy_model.index(0, 1))
    assert isinstance(delegate, DateTimeDelegate)

    # Check that the stop value is constraint by the start value of the frame.

    table.view.edit(index)
    assert delegate.editor.isVisible()
    assert (delegate.editor.dateTime().toString("yyyy-MM-dd hh:mm") ==
            '2018-06-13 12:00')

    delegate.editor.setDateTime(qdatetime_from_str('2018-06-13 03:00'))
    with qtbot.waitSignal(table.view.proxy_model.sig_sourcemodel_changed):
        qtbot.keyPress(delegate.editor, Qt.Key_Enter)

    assert (overview.model.client.frames[4].stop.format('YYYY-MM-DD HH:mm') ==
            '2018-06-13 06:00')

    # Check that the stop value is contraint by the start value of the
    # next frame.

    table.view.edit(index)
    assert delegate.editor.isVisible()
    assert (delegate.editor.dateTime().toString("yyyy-MM-dd hh:mm") ==
            '2018-06-13 06:00')

    delegate.editor.setDateTime(qdatetime_from_str('2018-06-13 21:45'))
    with qtbot.waitSignal(table.view.proxy_model.sig_sourcemodel_changed):
        qtbot.keyPress(delegate.editor, Qt.Key_Enter)

    assert (overview.model.client.frames[4].stop.format('YYYY-MM-DD HH:mm') ==
            '2018-06-13 18:00')


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
