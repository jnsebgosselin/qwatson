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
from qwatson.utils.fileio import delete_folder_recursively
from qwatson.utils.dates import local_arrow_from_tuple, qdatetime_from_str
from qwatson.models.delegates import (
    ToolButtonDelegate, TagEditDelegate, LineEditDelegate)


APPDIR = osp.join(osp.dirname(__file__), 'appdir1')
APPDIR2 = osp.join(osp.dirname(__file__), 'appdir2')


# ---- Test QWatson main window

def test_mainwindow_init(qtbot):
    """
    Test that the QWatson main widget and avtivity overview widgets are
    started correctly.
    """
    delete_folder_recursively(APPDIR, delroot=True)

    qwatson = QWatson(APPDIR)
    qtbot.addWidget(qwatson)
    qtbot.addWidget(qwatson.overview_widg)
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    assert qwatson
    assert qwatson.client.frames_file == osp.join(APPDIR, 'frames')

    qtbot.mouseClick(qwatson.btn_report, Qt.LeftButton)
    qtbot.waitForWindowShown(qwatson.overview_widg)

    # Check the default values.

    assert qwatson.currentProject() == ''
    assert qwatson.tag_manager.tags == []
    assert qwatson.comment_manager.text() == ''
    assert qwatson.round_time_btn.text() == 'round to 5min'
    assert qwatson.start_from.text() == 'start from now'

    qwatson.close()


def test_add_first_project(qtbot, mocker):
    """
    Test adding a new project and starting/stopping the timer to add an
    activity to the database for the first time.
    """
    qwatson = QWatson(APPDIR)
    qtbot.addWidget(qwatson)
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    # ---- Setup the activity input dialog

    # Setup the tags

    qtbot.keyClicks(qwatson.tag_manager, 'tag1, tag2, tag3')
    qtbot.keyPress(qwatson.tag_manager, Qt.Key_Enter)
    assert qwatson.tag_manager.tags == ['tag1', 'tag2', 'tag3']

    # Setup the comment

    qtbot.keyClicks(qwatson.comment_manager, 'First activity')
    qtbot.keyPress(qwatson.comment_manager, Qt.Key_Enter)
    assert qwatson.comment_manager.text() == 'First activity'

    # Add a new project

    qtbot.mouseClick(qwatson.project_manager.btn_add, Qt.LeftButton)
    qtbot.keyClicks(qwatson.project_manager.project_cbox.linedit, 'project1')
    qtbot.keyPress(qwatson.project_manager.project_cbox.linedit, Qt.Key_Enter)
    assert qwatson.currentProject() == 'project1'

    # ---- Add first activity

    assert len(qwatson.client.frames) == 0

    # Start the activity timer
    start = local_arrow_from_tuple((2018, 6, 14, 15, 59, 54))
    mocker.patch('arrow.now', return_value=start)
    qtbot.mouseClick(qwatson.btn_startstop, Qt.LeftButton)
    assert qwatson.elap_timer.is_started

    # Stop the activity timer
    stop = local_arrow_from_tuple((2018, 6, 14, 17, 12, 35))
    mocker.patch('arrow.now', return_value=stop)
    qtbot.mouseClick(qwatson.btn_startstop, Qt.LeftButton)
    assert not qwatson.elap_timer.is_started

    # Assert frame logged data
    assert len(qwatson.client.frames) == 1
    frame = qwatson.client.frames[0]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 16:00'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 17:15'
    assert frame.tags == ['tag1', 'tag2', 'tag3']
    assert frame.message == 'First activity'
    assert frame.project == 'project1'

    qwatson.close()


def test_load_config(qtbot, mocker):
    """
    Test that the activity fields are set correctly when starting QWatson and
    a frames file already exists.
    """
    qwatson = QWatson(APPDIR)
    qtbot.addWidget(qwatson)
    assert len(qwatson.client.frames) == 1
    qwatson.show()

    assert qwatson.currentProject() == 'project1'
    assert qwatson.tag_manager.tags == ['tag1', 'tag2', 'tag3']
    assert qwatson.comment_manager.text() == 'First activity'
    assert qwatson.round_time_btn.text() == 'round to 5min'
    qwatson.close()


def test_rename_project(qtbot, mocker):
    """Test that renaming a project works as expected."""
    qwatson = QWatson(APPDIR)
    qtbot.addWidget(qwatson)
    qwatson.show()
    project_manager = qwatson.project_manager

    # Enter edit mode, but do not change the project name.

    qtbot.mouseClick(project_manager.btn_rename, Qt.LeftButton)

    assert project_manager.project_cbox.linedit.isVisible()
    assert not project_manager.project_cbox.combobox.isVisible()
    qtbot.keyPress(project_manager.project_cbox.linedit, Qt.Key_Enter)
    assert not project_manager.project_cbox.linedit.isVisible()
    assert project_manager.project_cbox.combobox.isVisible()

    assert qwatson.currentProject() == 'project1'
    assert qwatson.client.frames[0].project == 'project1'

    # Enter edit mode and change the project name.

    qtbot.mouseClick(project_manager.btn_rename, Qt.LeftButton)

    assert project_manager.project_cbox.linedit.isVisible()
    assert not project_manager.project_cbox.combobox.isVisible()
    qtbot.keyPress(project_manager.project_cbox.linedit, Qt.Key_End)
    qtbot.keyClicks(project_manager.project_cbox.linedit, '_renamed')
    qtbot.keyPress(project_manager.project_cbox.linedit, Qt.Key_Enter)
    assert not project_manager.project_cbox.linedit.isVisible()
    assert project_manager.project_cbox.combobox.isVisible()

    assert qwatson.currentProject() == 'project1_renamed'
    assert qwatson.client.frames[0].project == 'project1_renamed'

    # Cancel the renaming of a project by pressing Escape

    qtbot.mouseClick(project_manager.btn_rename, Qt.LeftButton)

    assert project_manager.project_cbox.linedit.isVisible()
    assert not project_manager.project_cbox.combobox.isVisible()
    qtbot.keyClicks(project_manager.project_cbox.linedit, 'dummy')
    qtbot.keyPress(project_manager.project_cbox.linedit, Qt.Key_Escape)
    assert not project_manager.project_cbox.linedit.isVisible()
    assert project_manager.project_cbox.combobox.isVisible()

    assert qwatson.currentProject() == 'project1_renamed'
    assert qwatson.client.frames[0].project == 'project1_renamed'

    qwatson.close()


def test_start_from_last_when_later_than_now(qtbot, mocker):
    """
    Test that starting a new activity with the option 'start from' set to
    'last' is working as expected when the stop time of the last saved
    activity is later than current time (See Issue #53 and PR #54).
    """
    now = local_arrow_from_tuple((2018, 6, 14, 17, 13, 43))
    mocker.patch('arrow.now', return_value=now)
    mocker.patch('time.time', return_value=now.timestamp)

    mainwindow = QWatson(APPDIR)
    qtbot.addWidget(mainwindow)
    mainwindow.show()

    mainwindow.start_from.setCurrentIndex(1)
    assert mainwindow.start_from.text() == 'start from last'

    # Start the activity

    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert mainwindow.elap_timer.is_started
    assert round(mainwindow.elap_timer._elapsed_time) == 0

    # Stop the activity

    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert not mainwindow.elap_timer.is_started

    frame = mainwindow.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 17:15'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 17:15'


def test_start_from_last(qtbot, mocker):
    """
    Test that starting an activity with the option 'start from' set to 'last'
    works as expected.
    """
    now = local_arrow_from_tuple((2018, 6, 14, 18, 47, 23))
    mocker.patch('arrow.now', return_value=now)

    mainwindow = QWatson(APPDIR)
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

    mainwindow = QWatson(APPDIR)
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

    qtbot.mouseClick(datetime_dial.buttons['Cancel'], Qt.LeftButton)
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
    qtbot.mouseClick(datetime_dial.buttons['Ok'], Qt.LeftButton)
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

    mainwindow = QWatson(APPDIR)
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

    qtbot.mouseClick(mainwindow.close_dial.buttons['Cancel'], Qt.LeftButton)
    assert mainwindow.client.is_started
    assert mainwindow.currentIndex() == 0
    assert mainwindow.isVisible()
    assert not mainwindow.close_dial.isVisible()
    assert len(mainwindow.client.frames) == expected_framelen

    # Close QWatson and answer No in the dialog.

    mainwindow.close()
    assert mainwindow.currentIndex() == 2
    assert mainwindow.close_dial.isVisible()

    qtbot.mouseClick(mainwindow.close_dial.buttons['No'], Qt.LeftButton)
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

    qtbot.mouseClick(mainwindow.close_dial.buttons['Yes'], Qt.LeftButton)
    assert not mainwindow.client.is_started
    assert mainwindow.currentIndex() == 0
    assert not mainwindow.isVisible()

    frame = mainwindow.client.frames[-1]
    assert len(mainwindow.client.frames) == expected_framelen + 1
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:15'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:35'


# ---- Test import settings and data

def test_cancel_import_from_watson(qtbot, mocker):
    """
    Test that the dialog to import settings and data from Watson the first
    time QWatson is started is working as expected when the import is
    cancelled by the user.
    """
    now = local_arrow_from_tuple((2018, 6, 14, 19, 36, 23))
    mocker.patch('arrow.now', return_value=now)

    delete_folder_recursively(APPDIR2, delroot=True)
    os.environ['WATSON_DIR'] = APPDIR

    qwatson = QWatson(APPDIR2)
    qtbot.addWidget(qwatson)
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    # Assert that the import dialog it shown on first start.

    assert qwatson.import_dialog is not None
    assert qwatson.import_dialog.isVisible()

    # Answer Cancel in the import dialog and assert that the frames and that
    # the activity input dialog is empty.

    with qtbot.waitSignal(qwatson.import_dialog.destroyed):
        qtbot.mouseClick(qwatson.import_dialog.buttons['Cancel'],
                         Qt.LeftButton)

    assert qwatson.currentIndex() == 0
    assert qwatson.import_dialog is None

    assert len(qwatson.client.frames) == 0
    assert qwatson.currentProject() == ''
    assert qwatson.comment_manager.text() == ''
    assert qwatson.tag_manager.tags == []

    assert osp.exists(qwatson.client.frames_file)
    qwatson.close()


def test_import_from_watson_noshow(qtbot, mocker):
    """
    Test that the import from watson dialog is not shown the second time
    QWatson is started.
    """
    now = local_arrow_from_tuple((2018, 6, 14, 19, 36, 23))
    mocker.patch('arrow.now', return_value=now)

    os.environ['WATSON_DIR'] = APPDIR

    qwatson = QWatson(APPDIR2)
    qtbot.addWidget(qwatson)
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    # Assert that the import from Watson dialog is not shown on the second run.

    assert qwatson.import_dialog is None
    assert qwatson.currentIndex() == 0

    table = qwatson.overview_widg.table_widg.tables[3]
    assert len(qwatson.client.frames) == 0
    assert table.view.proxy_model.get_accepted_row_count() == 0

    assert qwatson.currentProject() == ''
    assert qwatson.comment_manager.text() == ''
    assert qwatson.tag_manager.tags == []


def test_accept_import_from_watson(qtbot, mocker):
    """
    Test that the dialog to import settings and data from Watson the first
    time QWatson is started is working as expected when the import is
    accepted by the user.
    """
    now = local_arrow_from_tuple((2018, 6, 14, 19, 36, 23))
    mocker.patch('arrow.now', return_value=now)

    delete_folder_recursively(APPDIR2, delroot=True)
    os.environ['WATSON_DIR'] = APPDIR

    qwatson = QWatson(APPDIR2)
    qtbot.addWidget(qwatson)
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    # Assert that the import dialog it shown.

    assert qwatson.import_dialog is not None
    assert qwatson.import_dialog.isVisible()

    # Answer Import in the import dialog and assert that the frames and that
    # the activity input dialog data.

    with qtbot.waitSignal(qwatson.import_dialog.destroyed):
        qtbot.mouseClick(qwatson.import_dialog.buttons['Import'],
                         Qt.LeftButton)

    assert qwatson.import_dialog is None
    assert qwatson.currentIndex() == 0

    table = qwatson.overview_widg.table_widg.tables[3]
    assert len(qwatson.client.frames) == 5
    assert table.view.proxy_model.get_accepted_row_count() == 5

    assert qwatson.currentProject() == 'project1_renamed'
    assert qwatson.comment_manager.text() == 'First activity'
    assert qwatson.tag_manager.tags == ['tag1', 'tag2', 'tag3']

    qwatson.close()


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
    state_filename = osp.join(APPDIR2, 'state')
    with open(state_filename, 'w') as f:
        f.write(content)

    now = local_arrow_from_tuple((2018, 6, 14, 19, 45, 17))
    mocker.patch('arrow.now', return_value=now)

    # Open QWatson and assert an error frame is added correctly to
    # the database

    qwatson = QWatson(APPDIR2)
    qtbot.addWidget(qwatson)
    qwatson.show()

    frame = qwatson.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 17:15'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 19:45'

    assert qwatson.currentProject() == 'test_error'
    assert frame.project == 'test_error'

    assert qwatson.tag_manager.tags == ['error']
    assert frame.tags == ['error']

    expected_comment = "last session not closed correctly."
    assert qwatson.comment_manager.text() == expected_comment
    assert frame.message == expected_comment


# ---- Test QWatson overview table

def test_show_overview_table(qtbot):
    """
    Test that the overview table window is shown and focused as expected when
    clicking on the 'Activity Overview' button on the mainwindow.
    """
    mainwindow = QWatson(APPDIR2)
    qtbot.addWidget(mainwindow)
    mainwindow.show()

    overview_window = mainwindow.overview_widg
    qtbot.addWidget(overview_window)

    qtbot.mouseClick(mainwindow.btn_report, Qt.LeftButton)
    qtbot.waitForWindowShown(overview_window)

    assert overview_window.hasFocus()

    # Give focus to the main window, then click on the btn_report and assert
    # that the focus is given back to the overview window.

    mainwindow.activateWindow()
    mainwindow.raise_()
    mainwindow.setFocus()

    assert not overview_window.hasFocus()
    qtbot.mouseClick(mainwindow.btn_report, Qt.LeftButton)
    assert overview_window.hasFocus()

    # Minimize the overview window and restore it by clicking on btn_report.

    overview_window.showMinimized()
    assert overview_window.isMinimized()
    assert not overview_window.isActiveWindow()
    assert not overview_window.hasFocus()

    qtbot.mouseClick(mainwindow.btn_report, Qt.LeftButton)
    assert overview_window.hasFocus()
    assert overview_window.isActiveWindow()

    # Maximize and minimize the overview window to the taskbar,
    # then restore it by clicking on btn_report.

    overview_window.showMaximized()
    overview_window.showMinimized()
    assert overview_window.isMaximized()
    assert overview_window.isMinimized()
    assert not overview_window.isActiveWindow()
    assert not overview_window.hasFocus()

    qtbot.mouseClick(mainwindow.btn_report, Qt.LeftButton)
    assert overview_window.isMaximized()
    assert not overview_window.isMinimized()
    assert overview_window.isActiveWindow()
    assert overview_window.hasFocus()


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
