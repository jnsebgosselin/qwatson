# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import os
import os.path as osp
import json

# ---- Third party imports

import pytest
from PyQt5.QtCore import Qt

# ---- Local imports

from qwatson.widgets.tableviews import QMessageBox
from qwatson.mainwindow import QWatson
from qwatson.utils.fileio import delete_file_safely
from qwatson.utils.dates import local_arrow_from_tuple, qdatetime_from_str
from qwatson.models.delegates import (StartDelegate, StopDelegate,
                                      ToolButtonDelegate)


WORKDIR = osp.dirname(__file__)
FRAMEFILE = osp.join(WORKDIR, 'frames')
STATEFILE = osp.join(WORKDIR, 'state')


# Test QWatson central widget
# -------------------------------

def test_mainwindow_init(qtbot):
    """
    Test that the QWatson main widget and avtivity overview widgets are
    started correctly.
    """
    frames_file = osp.join(WORKDIR, 'frames')
    delete_file_safely(FRAMEFILE)
    delete_file_safely(FRAMEFILE + '.bak')
    delete_file_safely(STATEFILE)
    delete_file_safely(STATEFILE + '.bak')
    qtbot.waitUntil(lambda: not osp.exists(frames_file))

    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    qtbot.addWidget(mainwindow.overview_widg)
    mainwindow.show()

    assert mainwindow
    assert mainwindow.client.frames_file == frames_file

    qtbot.mouseClick(mainwindow.btn_report, Qt.LeftButton)
    assert mainwindow.overview_widg.isVisible()
    mainwindow.close()


def test_add_first_project(qtbot, mocker):
    """
    Test adding a new project and starting/stopping the timer to add an
    activity to the database for the first time.
    """
    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    mainwindow.show()
    qtbot.waitForWindowShown(mainwindow)

    # ---- Check default

    activity_input_dial = mainwindow.activity_input_dial
    assert activity_input_dial.project == ''
    assert activity_input_dial.tags == []
    assert activity_input_dial.comment == ''
    assert mainwindow.round_time_btn.text() == 'round to 5min'
    assert mainwindow.start_from.text() == 'start from now'

    # ---- Setup the activity input dialog

    # Setup the tags
    qtbot.keyClicks(activity_input_dial.tag_lineedit, 'tag1, tag2, tag3')
    qtbot.keyPress(activity_input_dial.tag_lineedit, Qt.Key_Enter)
    assert activity_input_dial.tags == ['tag1', 'tag2', 'tag3']

    # Setup the comment
    qtbot.keyClicks(activity_input_dial.msg_textedit, 'First activity')
    qtbot.keyPress(activity_input_dial.msg_textedit, Qt.Key_Enter)
    assert activity_input_dial.comment == 'First activity'

    # Add a new project
    qtbot.mouseClick(
        activity_input_dial.project_manager.btn_add, Qt.LeftButton)
    qtbot.keyClicks(
        activity_input_dial.project_manager.project_cbox.linedit, 'project1')
    qtbot.keyPress(
        activity_input_dial.project_manager.project_cbox.linedit, Qt.Key_Enter)
    assert activity_input_dial.project == 'project1'

    # ---- Add first activity

    assert len(mainwindow.client.frames) == 0

    # Start the activity timer
    start = local_arrow_from_tuple((2018, 6, 14, 15, 59, 54))
    mocker.patch('arrow.now', return_value=start)
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert mainwindow.elap_timer.is_started

    # Stop the activity timer
    stop = local_arrow_from_tuple((2018, 6, 14, 17, 12, 35))
    mocker.patch('arrow.now', return_value=stop)
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert not mainwindow.elap_timer.is_started

    # Assert frame logged data
    assert len(mainwindow.client.frames) == 1
    frame = mainwindow.client.frames[0]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 16:00'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 17:15'
    assert frame.tags == ['tag1', 'tag2', 'tag3']
    assert frame.message == 'First activity'
    assert frame.project == 'project1'

    mainwindow.close()


def test_load_config(qtbot, mocker):
    """
    Test that the activity fields are set correctly when starting QWatson and
    a frames file already exists.
    """
    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    assert len(mainwindow.client.frames) == 1
    mainwindow.show()

    activity_input_dial = mainwindow.activity_input_dial
    assert activity_input_dial.project == 'project1'
    assert activity_input_dial.tags == ['tag1', 'tag2', 'tag3']
    assert activity_input_dial.comment == 'First activity'
    assert mainwindow.round_time_btn.text() == 'round to 5min'
    mainwindow.close()


def test_rename_project(qtbot, mocker):
    """Test that renaming a project works as expected."""
    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    mainwindow.show()
    project_manager = mainwindow.activity_input_dial.project_manager

    # Enter edit mode, but do not change the project name.

    qtbot.mouseClick(project_manager.btn_rename, Qt.LeftButton)

    assert project_manager.project_cbox.linedit.isVisible()
    assert not project_manager.project_cbox.combobox.isVisible()
    qtbot.keyPress(project_manager.project_cbox.linedit, Qt.Key_Enter)
    assert not project_manager.project_cbox.linedit.isVisible()
    assert project_manager.project_cbox.combobox.isVisible()

    assert mainwindow.activity_input_dial.project == 'project1'
    assert mainwindow.client.frames[0].project == 'project1'

    # Enter edit mode and change the project name.

    qtbot.mouseClick(project_manager.btn_rename, Qt.LeftButton)

    assert project_manager.project_cbox.linedit.isVisible()
    assert not project_manager.project_cbox.combobox.isVisible()
    qtbot.keyClicks(project_manager.project_cbox.linedit, '_renamed')
    qtbot.keyPress(project_manager.project_cbox.linedit, Qt.Key_Enter)
    assert not project_manager.project_cbox.linedit.isVisible()
    assert project_manager.project_cbox.combobox.isVisible()

    assert mainwindow.activity_input_dial.project == 'project1_renamed'
    assert mainwindow.client.frames[0].project == 'project1_renamed'
    mainwindow.close()


def test_start_from_last(qtbot, mocker):
    """
    Test that starting an activity with the option 'start from' set to 'last'
    works as expected.
    """
    now = local_arrow_from_tuple((2018, 6, 14, 18, 47, 23))
    mocker.patch('arrow.now', return_value=now)

    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    mainwindow.show()

    mainwindow.start_from.setCurrentIndex(1)
    assert mainwindow.start_from.text() == 'start from last'

    # Start and stop the activity timer
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert mainwindow.elap_timer.is_started
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert not mainwindow.elap_timer.is_started

    frame = mainwindow.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 17:15'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 18:45'


def test_start_from_other(qtbot, mocker):
    """
    Test that starting an activity with the option 'start from' set to 'other'
    works as expected.
    """
    now = local_arrow_from_tuple((2018, 6, 14, 19, 12, 36))
    mocker.patch('arrow.now', return_value=now)

    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    mainwindow.show()

    initial_frames_len = len(mainwindow.client.frames)
    datetime_dial = mainwindow.datetime_input_dial

    mainwindow.start_from.setCurrentIndex(2)
    assert mainwindow.start_from.text() == 'start from other'
    assert not datetime_dial.isVisible()

    # Start the activity timer and assert the datetime dialog is shown
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert not mainwindow.elap_timer.is_started
    assert datetime_dial.isVisible()
    datetime_arrow = datetime_dial.get_datetime_arrow()
    assert datetime_arrow.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:12'
    minimum_datetime = datetime_dial.minimum_datetime
    assert minimum_datetime.format('YYYY-MM-DD HH:mm') == '2018-06-14 18:45'

    # Cancel the dialog and assert it is working as expected.
    qtbot.mouseClick(datetime_dial.button_box.buttons()[1], Qt.LeftButton)
    assert not mainwindow.elap_timer.is_started
    assert not datetime_dial.isVisible()
    assert not mainwindow.client.is_started
    assert len(mainwindow.client.frames) == initial_frames_len

    # Start the activity timer again and assert the datetime dialog is shown
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert not mainwindow.elap_timer.is_started
    assert datetime_dial.isVisible()

    # Change the datetime below the minimum value.
    datetime_dial.datetime_edit.setDateTime(
        qdatetime_from_str('2018-06-14 18:25'))
    datetime_arrow = datetime_dial.get_datetime_arrow()
    assert datetime_arrow.format('YYYY-MM-DD HH:mm') == '2018-06-14 18:45'

    # Change the datetime above now.
    datetime_dial.datetime_edit.setDateTime(
        qdatetime_from_str('2018-06-14 21:35'))
    datetime_arrow = datetime_dial.get_datetime_arrow()
    assert datetime_arrow.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:12'

    # Change the datetime and accept and assert the dialog is not visible
    # and the activity is correctly started.
    datetime_dial.datetime_edit.setDateTime(
        qdatetime_from_str('2018-06-14 19:01'))
    qtbot.mouseClick(datetime_dial.button_box.buttons()[0], Qt.LeftButton)
    assert mainwindow.elap_timer.is_started
    assert not datetime_dial.isVisible()
    assert mainwindow.client.is_started

    # Stop the activity and assert it was saved correctly.
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert not mainwindow.elap_timer.is_started
    assert not mainwindow.client.is_started
    assert len(mainwindow.client.frames) == initial_frames_len + 1
    frame = mainwindow.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:00'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:15'


def test_close_when_running(qtbot, mocker):
    """
    Test that the dialog that ask the user what to do when closing QWatson
    while an activity is running is working as expected.
    """
    now = local_arrow_from_tuple((2018, 6, 14, 19, 36, 23))
    mocker.patch('arrow.now', return_value=now)

    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    mainwindow.show()
    qtbot.waitForWindowShown(mainwindow)
    expected_framelen = len(mainwindow.client.frames)

    # Start tracking the activity from last

    mainwindow.start_from.setCurrentIndex(1)
    assert mainwindow.start_from.text() == 'start from last'

    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert mainwindow.currentIndex() == 0
    assert mainwindow.client.is_started

    # Close QWatson and answer Cancel in the dialog.

    mainwindow.close()
    assert mainwindow.currentIndex() == 2
    assert mainwindow.close_dial.isVisible()

    qtbot.mouseClick(mainwindow.close_dial.cancel_btn, Qt.LeftButton)
    assert mainwindow.client.is_started
    assert mainwindow.currentIndex() == 0
    assert mainwindow.isVisible()
    assert not mainwindow.close_dial.isVisible()
    assert len(mainwindow.client.frames) == expected_framelen

    # Close QWatson and answer No in the dialog.

    mainwindow.close()
    assert mainwindow.currentIndex() == 2
    assert mainwindow.close_dial.isVisible()

    qtbot.mouseClick(mainwindow.close_dial.no_btn, Qt.LeftButton)
    assert not mainwindow.client.is_started
    assert not mainwindow.isVisible()
    assert len(mainwindow.client.frames) == expected_framelen

    # Restart QWatson and start the tracker.

    mainwindow.show()
    qtbot.waitForWindowShown(mainwindow)
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert mainwindow.currentIndex() == 0
    assert mainwindow.client.is_started

    # Close QWatson and answer Yes in the dialog.

    mainwindow.close()
    assert mainwindow.currentIndex() == 2
    assert mainwindow.close_dial.isVisible()

    qtbot.mouseClick(mainwindow.close_dial.yes_btn, Qt.LeftButton)
    assert not mainwindow.client.is_started
    assert mainwindow.currentIndex() == 0
    assert not mainwindow.isVisible()

    frame = mainwindow.client.frames[-1]
    assert len(mainwindow.client.frames) == expected_framelen + 1
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:15'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:35'


def test_last_closed_error(qtbot, mocker):
    """
    Test that QWatson opens correctly when the last session was not closed
    properly
    """
    # Create a state file.

    start = local_arrow_from_tuple((2018, 6, 14, 17, 12, 35))
    state = {'project': 'test_error',
             'start': start.to('utc').timestamp,
             'tags': ['test'],
             'message': 'test error last close'}
    content = json.dumps(state)
    state_filename = osp.join(WORKDIR, 'state')
    with open(state_filename, 'w') as f:
        f.write(content)

    now = local_arrow_from_tuple((2018, 6, 14, 19, 45, 17))
    mocker.patch('arrow.now', return_value=now)

    # Open QWatson and assert an error frame is added correctly to
    # the database

    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    mainwindow.show()

    frame = mainwindow.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 17:15'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:45'

    assert mainwindow.activity_input_dial.project == 'test_error'
    assert frame.project == 'test_error'

    assert mainwindow.activity_input_dial.tags == ['error']
    assert frame.tags == ['error']

    expected_comment = "last session not closed correctly."
    assert mainwindow.activity_input_dial.comment == expected_comment
    assert frame.message == expected_comment


# Test QWatson overview table
# -------------------------------

def test_delete_frame(qtbot, mocker):
    """
    Test that deleting a frame from the activity overview table work correctly.
    """
    now = local_arrow_from_tuple((2018, 6, 14, 23, 59, 0))
    mocker.patch('arrow.now', return_value=now)

    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    qtbot.addWidget(mainwindow.overview_widg)
    mainwindow.show()
    expected_rowcount = len(mainwindow.client.frames)

    qtbot.mouseClick(mainwindow.btn_report, Qt.LeftButton)
    qtbot.waitForWindowShown(mainwindow.overview_widg)
    assert mainwindow.overview_widg.isVisible()

    # Find the table where the last frame is stored.

    table_widg = mainwindow.overview_widg.table_widg
    fstart_day = mainwindow.client.frames[-1].start.floor('day')
    for i, table in enumerate(table_widg.tables):
        if table.date_span[0] == fstart_day:
            break
    assert i == 3
    assert table.view.proxy_model.get_accepted_row_count() == expected_rowcount
    assert 'error' in mainwindow.client.tags

    row = expected_rowcount - 1
    col = table.view.proxy_model.sourceModel().COLUMNS['icons']
    index = table.view.proxy_model.index(row, col)
    delegate = table.view.itemDelegate(index)
    assert isinstance(delegate, ToolButtonDelegate)

    # Create an event to simulate a mouss press because it is not working
    # when using qtbot.mousePress.

    visual_rect = table.view.visualRect(index)

    # Click to delete last frame and answer No.

    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)
    with qtbot.waitSignal(table.view.proxy_model.sig_btn_delrow_clicked):
        qtbot.mouseClick(table.view.viewport(), Qt.LeftButton,
                         pos=visual_rect.center())

    assert table.view.proxy_model.get_accepted_row_count() == expected_rowcount
    assert len(mainwindow.client.frames) == expected_rowcount
    assert 'error' in mainwindow.client.tags

    # Click to delete last frame and answer Yes.

    expected_rowcount += -1
    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    with qtbot.waitSignal(table.view.proxy_model.sig_btn_delrow_clicked):
        qtbot.mouseClick(table.view.viewport(), Qt.LeftButton,
                         pos=visual_rect.center())

    assert table.view.proxy_model.get_accepted_row_count() == expected_rowcount
    assert len(mainwindow.client.frames) == expected_rowcount
    assert 'error' not in mainwindow.client.tags

    mainwindow.close()


def test_edit_start_stop(qtbot, mocker):
    """
    Test editing start and stop date in the activity overview table.
    """
    now = local_arrow_from_tuple((2018, 6, 14, 23, 59, 0))
    mocker.patch('arrow.now', return_value=now)

    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
    qtbot.addWidget(mainwindow.overview_widg)
    mainwindow.show()

    qtbot.mouseClick(mainwindow.btn_report, Qt.LeftButton)
    qtbot.waitForWindowShown(mainwindow.overview_widg)

    table_widg = mainwindow.overview_widg.table_widg

    # Find the table where the first frame is stored.

    fstart_day = mainwindow.client.frames[0].start.floor('day')
    for i, table in enumerate(table_widg.tables):
        if table.date_span[0] == fstart_day:
            break
    assert i == 3

    # ---- Edit frame start

    old_start = '2018-06-14 16:00'
    fstart = mainwindow.client.frames[0].start.format('YYYY-MM-DD HH:mm')
    assert fstart == old_start

    index = table.view.proxy_model.index(0, 0)
    delegate = table.view.itemDelegate(index)
    assert isinstance(delegate, StartDelegate)

    # Assert the delegate displayed value.
    table.view.edit(index)
    assert old_start == delegate.editor.dateTime().toString("yyyy-MM-dd hh:mm")

    # The new start must be in the same day as the old start, or otherwise,
    # the current table will become empty after the change.
    new_start = '2018-06-14 12:23'
    delegate.editor.setDateTime(qdatetime_from_str(new_start))
    with qtbot.waitSignal(table.view.proxy_model.sig_sourcemodel_changed):
        qtbot.keyPress(delegate.editor, Qt.Key_Enter)

    fstart = mainwindow.client.frames[0].start.format('YYYY-MM-DD HH:mm')
    assert fstart == new_start

    # ---- Edit frame stop

    old_stop = '2018-06-14 17:15'
    fstop = mainwindow.client.frames[0].stop.format('YYYY-MM-DD HH:mm')
    assert fstop == old_stop

    index = table.view.proxy_model.index(0, 1)
    delegate = table.view.itemDelegate(table.view.proxy_model.index(0, 1))
    assert isinstance(delegate, StopDelegate)

    # Assert the delegate displayed value.
    table.view.edit(index)
    assert old_stop == delegate.editor.dateTime().toString("yyyy-MM-dd hh:mm")

    # The new stop must not be later than the start time of the activity
    # added in test_start_from_last.
    new_stop = '2018-06-14 16:43'
    delegate.editor.setDateTime(qdatetime_from_str(new_stop))
    with qtbot.waitSignal(table.view.proxy_model.sig_sourcemodel_changed):
        qtbot.keyPress(delegate.editor, Qt.Key_Enter)

    fstop = mainwindow.client.frames[0].stop.format('YYYY-MM-DD HH:mm')
    assert fstop == new_stop

    mainwindow.close()


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
