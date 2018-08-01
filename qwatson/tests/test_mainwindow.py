# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

"""
Tests for the mainwindow.
"""

# ---- Standard imports

import os
import os.path as osp
import json

# ---- Third party imports

import arrow
import pytest
from PyQt5.QtCore import Qt

# ---- Local imports

from qwatson.mainwindow import QWatson
from qwatson.utils.dates import (local_arrow_from_tuple, qdatetime_from_arrow,
                                 qdatetime_from_str, round_arrow_to)
from qwatson.utils.fileio import delete_folder_recursively


@pytest.fixture(scope="module")
def now():
    return local_arrow_from_tuple((2018, 7, 30, 7, 23, 44))


@pytest.fixture()
def appdir(now):
    # We do not use the tmpdir_factory fixture because we use the files
    # produces by the tests to test QWatson locally.

    appdir = osp.join(osp.dirname(__file__), 'appdir', 'mainwindow')
    delete_folder_recursively(appdir)
    if not osp.exists(appdir):
        os.makedirs(appdir)

    # Create the frames file.

    frames = [[round_arrow_to(now.shift(hours=-3), 5).timestamp,
               round_arrow_to(now, 5).timestamp,
               "p1",
               "e22fe653844442bab09a109f086688ec",
               ["tag1", "tag2", "tag3"], now.timestamp, "First activity"]]
    with open(osp.join(appdir, 'frames'), 'w') as f:
        f.write(json.dumps(frames))

    return appdir


@pytest.fixture(scope="module")
def newdir(now):
    appdir_empty = osp.join(osp.dirname(__file__), 'appdir', 'new')
    delete_folder_recursively(appdir_empty)
    return appdir_empty


@pytest.fixture
def qwatson_bot(qtbot, mocker, appdir, now):
    def _create_bot(qwatson_dir=appdir, watson_dir=appdir, now=now):
        mocker.patch('arrow.now', return_value=now)
        mocker.patch('time.time', return_value=now.timestamp)
        os.environ['QWATSON_DIR'] = qwatson_dir
        os.environ['WATSON_DIR'] = watson_dir

        qwatson = QWatson()
        qtbot.addWidget(qwatson)
        qwatson.show()
        qtbot.waitForWindowShown(qwatson)

        return qwatson, qtbot, mocker
    return _create_bot


# ---- Test Init and Defaults


def test_init_and_defaults(qwatson_bot):
    """Test that the stopwatch widget is initialized as expected."""
    qwatson, qtbot, mocker = qwatson_bot()
    stopwatch = qwatson.stopwatch

    assert stopwatch.buttons['start'].isEnabled()
    assert not stopwatch.buttons['stop'].isEnabled()
    assert not stopwatch.buttons['cancel'].isEnabled()
    assert stopwatch.isRunning() is False
    assert stopwatch.elap_timer._elapsed_time == 0
    assert qwatson.startFrom() == 'now'
    assert qwatson.roundTo() == 5

    assert len(qwatson.client.frames) == 1
    frame = qwatson.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-07-30 04:25'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-07-30 07:25'
    assert frame.message == 'First activity'
    assert frame.tags == ["tag1", "tag2", "tag3"]
    assert frame.project == 'p1'

    assert qwatson.currentProject() == 'p1'
    assert qwatson.tag_manager.tags == ['tag1', 'tag2', 'tag3']
    assert qwatson.comment_manager.text() == 'First activity'


def test_last_closed_error(qwatson_bot, appdir, now):
    """
    Test that QWatson opens correctly when the last session was not closed
    properly
    """
    # Add a non-empty state file to the appdir folder before creating the
    # qwatson bot :

    state = {'project': 'test_error',
             'start': round_arrow_to(now, 5).timestamp,
             'tags': ['test'],
             'message': 'test error last close'}

    content = json.dumps(state)
    with open(osp.join(appdir, 'state'), 'w') as f:
        f.write(content)

    qwatson, qtbot, mocker = qwatson_bot(qwatson_dir=appdir,
                                         now=now.shift(hours=5))

    # Open QWatson and assert an error frame is added correctly to
    # the database

    assert len(qwatson.client.frames) == 2

    frame = qwatson.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-07-30 07:25'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-07-30 12:25'

    assert qwatson.currentProject() == 'test_error'
    assert frame.project == 'test_error'

    assert qwatson.tag_manager.tags == ['error']
    assert frame.tags == ['error']

    expected_comment = "last session not closed correctly."
    assert qwatson.comment_manager.text() == expected_comment
    assert frame.message == expected_comment


# ---- Test Project

def test_add_project(qwatson_bot):
    """Test adding a new project without adding a new activity."""
    qwatson, qtbot, mocker = qwatson_bot()

    assert qwatson.client.projects == ['', 'p1']
    assert qwatson.currentProject() == 'p1'

    # Add a new project

    qtbot.mouseClick(qwatson.project_manager.btn_add, Qt.LeftButton)
    qtbot.keyClicks(qwatson.project_manager.project_cbox.linedit, 'p2')
    qtbot.keyPress(qwatson.project_manager.project_cbox.linedit, Qt.Key_Enter)
    assert qwatson.currentProject() == 'p2'
    assert qwatson.client.projects == ['', 'p1', 'p2']

    # Assert the new project was saved correctly to file.

    projects = qwatson.client._load_json_file(
        qwatson.client.projects_file, type=list)
    assert projects == ['', 'p1', 'p2']

# ---- Test Start / Stop / Cancel


def test_startstop(qwatson_bot, now):
    """
    Test that starting and stoping the monitoring of an activity work
    as expected.
    """
    qwatson, qtbot, mocker = qwatson_bot()

    # Start monitoring an activity.

    qtbot.mouseClick(qwatson.stopwatch.buttons['start'], Qt.LeftButton)
    assert not qwatson.btn_startfrom.isEnabled()
    assert not qwatson.stopwatch.buttons['start'].isEnabled()
    assert qwatson.stopwatch.buttons['stop'].isEnabled()
    assert qwatson.stopwatch.buttons['cancel'].isEnabled()
    assert qwatson.stopwatch.isRunning() is True
    assert qwatson.stopwatch.elap_timer._elapsed_time == 0

    # Setup project, tags, and comment.

    qwatson.setCurrentProject('p1')
    qwatson.tag_manager.set_tags(['test', 'start', 'stop'])
    qwatson.comment_manager.setText('Test start-stop')

    # Stop monitoring the activity 3 hours after it was started :

    mocker.patch('arrow.now', return_value=now.shift(hours=3))
    mocker.patch('time.time', return_value=arrow.now().timestamp)
    qtbot.wait(11)
    assert qwatson.stopwatch.elap_timer._elapsed_time == 3*60*60

    qtbot.mouseClick(qwatson.stopwatch.buttons['stop'], Qt.LeftButton)
    assert qwatson.btn_startfrom.isEnabled()
    assert qwatson.stopwatch.buttons['start'].isEnabled()
    assert not qwatson.stopwatch.buttons['stop'].isEnabled()
    assert not qwatson.stopwatch.buttons['cancel'].isEnabled()
    assert qwatson.stopwatch.isRunning() is False
    assert qwatson.stopwatch.elap_timer._elapsed_time == 3*60*60
    assert len(qwatson.client.frames) == 2

    frame = qwatson.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-07-30 07:25'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-07-30 10:25'
    assert frame.message == 'Test start-stop'
    assert frame.tags == ['start', 'stop', 'test']
    assert frame.project == 'p1'


def test_start_from_last(qwatson_bot, now):
    """
    Test that starting an activity with the option 'start from' set to 'last'
    works as expected.
    """
    qwatson, qtbot, mocker = qwatson_bot()

    qwatson.btn_startfrom.setCurrentIndex(1)
    assert qwatson.startFrom() == 'last'

    # Start the activity at 2018-07-30 08:23:44, 1 hour after the current now :

    mocker.patch('arrow.now', return_value=now.shift(hours=1))
    mocker.patch('time.time', return_value=arrow.now().timestamp)

    qtbot.mouseClick(qwatson.stopwatch.buttons['start'], Qt.LeftButton)
    assert qwatson.stopwatch.elap_timer.is_started
    assert qwatson.stopwatch.elap_timer._elapsed_time == (35+23)*60 + 44

    # Stop the activity at 2018-07-30 10:23:44, 2 hours after starting it :

    mocker.patch('arrow.now', return_value=now.shift(hours=3))
    qtbot.mouseClick(qwatson.stopwatch.buttons['stop'], Qt.LeftButton)
    frame = qwatson.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-07-30 07:25'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-07-30 10:25'


def test_start_from_last_when_later_than_now(qwatson_bot, now):
    """
    Test that starting a new activity with the option 'start from' set to
    'last' is working as expected when the stop time of the last saved
    activity is later than current time (See Issue #53 and PR #54).
    """
    qwatson, qtbot, mocker = qwatson_bot()

    qwatson.btn_startfrom.setCurrentIndex(1)
    assert qwatson.startFrom() == 'last'

    # The stop time of the previous activity is 2018-07-30 07:25 (because it
    # was rounded to 5 min) while the now time is 2018-07-30 07:23:44.

    # Start the activity :

    qtbot.mouseClick(qwatson.stopwatch.buttons['start'], Qt.LeftButton)
    assert qwatson.stopwatch.elap_timer.is_started
    assert qwatson.stopwatch.elap_timer._elapsed_time == 0

    # Stop the activity 2 hours after starting it :

    mocker.patch('arrow.now', return_value=now.shift(hours=3))
    qtbot.mouseClick(qwatson.stopwatch.buttons['stop'], Qt.LeftButton)
    frame = qwatson.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-07-30 07:25'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-07-30 10:25'


def test_start_from_other(qwatson_bot, now):
    """
    Test that starting an activity with the option 'start from' set to 'other'
    works as expected.
    """
    qwatson, qtbot, mocker = qwatson_bot()
    datetime_dial = qwatson.datetime_input_dial

    qwatson.btn_startfrom.setCurrentIndex(2)
    assert qwatson.startFrom() == 'other'
    assert not datetime_dial.isVisible()

    # Set now to 2018-07-30 10:23:44, 3 hours after the current now :

    mocker.patch('arrow.now', return_value=now.shift(hours=3))
    mocker.patch('time.time', return_value=arrow.now().timestamp)

    # Start the activity and assert the datetime dialog is shown :

    qtbot.mouseClick(qwatson.stopwatch.buttons['start'], Qt.LeftButton)
    assert datetime_dial.isVisible()
    assert (datetime_dial.get_datetime_arrow().format('YYYY-MM-DD HH:mm') ==
            arrow.now().format('YYYY-MM-DD HH:mm'))
    assert datetime_dial.minimum_datetime == qwatson.client.frames[-1].stop

    # Cancel the dialog :

    qtbot.mouseClick(datetime_dial.buttons['Cancel'], Qt.LeftButton)
    assert not datetime_dial.isVisible()
    assert not qwatson.client.is_started
    assert not qwatson.stopwatch.elap_timer.is_started
    assert qwatson.stopwatch.elap_timer._elapsed_time == 0
    assert len(qwatson.client.frames) == 1

    # Start the activity again :

    qtbot.mouseClick(qwatson.stopwatch.buttons['start'], Qt.LeftButton)
    assert datetime_dial.isVisible()

    # Change the datetime below the minimum value :

    datetime_dial.datetime_edit.setDateTime(qdatetime_from_arrow(
        datetime_dial.minimum_datetime.shift(hours=-3)))
    assert datetime_dial.get_datetime_arrow() == datetime_dial.minimum_datetime

    # Change the datetime above now :

    datetime_dial.datetime_edit.setDateTime(qdatetime_from_arrow(
            arrow.now().shift(hours=1)))
    assert (datetime_dial.get_datetime_arrow().format('YYYY-MM-DD HH:mm') ==
            arrow.now().format('YYYY-MM-DD HH:mm'))

    # Change the datetime to 2018-07-30 8:43 and start the activity :

    datetime_dial.datetime_edit.setDateTime(
        qdatetime_from_str('2018-07-30 08:43'))

    qtbot.mouseClick(datetime_dial.buttons['Start'], Qt.LeftButton)
    assert not datetime_dial.isVisible()
    assert qwatson.client.is_started
    assert qwatson.stopwatch.elap_timer.is_started
    assert qwatson.stopwatch.elap_timer._elapsed_time == (17+60+23)*60 + 44

    # Stop the activity :

    qtbot.mouseClick(qwatson.stopwatch.buttons['stop'], Qt.LeftButton)
    assert len(qwatson.client.frames) == 2
    frame = qwatson.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-07-30 08:45'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-07-30 10:25'


def test_startcancel(qwatson_bot, now):
    """
    Test that starting and cancelling the monitoring of an activity work
    as expected.
    """
    qwatson, qtbot, mocker = qwatson_bot()
    init_len = len(qwatson.client.frames)

    # Start monitoring an activity :

    now = qwatson.client.frames[-1].stop
    mocker.patch('arrow.now', return_value=now)
    mocker.patch('time.time', return_value=arrow.now().timestamp)

    qtbot.mouseClick(qwatson.stopwatch.buttons['start'], Qt.LeftButton)

    # There is no need to assert anything here since this was covered in the
    # previous test above.

    # Cancel monitoring the activity :

    mocker.patch('arrow.now', return_value=now.shift(hours=3))
    mocker.patch('time.time', return_value=arrow.now().timestamp)
    qtbot.wait(11)
    assert qwatson.stopwatch.elap_timer._elapsed_time == 3*60*60

    qtbot.mouseClick(qwatson.stopwatch.buttons['cancel'], Qt.LeftButton)
    assert qwatson.btn_startfrom.isEnabled()
    assert qwatson.stopwatch.buttons['start'].isEnabled()
    assert not qwatson.stopwatch.buttons['stop'].isEnabled()
    assert not qwatson.stopwatch.buttons['cancel'].isEnabled()
    assert qwatson.stopwatch.isRunning() is False
    assert qwatson.stopwatch.elap_timer._elapsed_time == 0

    assert len(qwatson.client.frames) == init_len


# ---- Test Import Settings and Data


def test_cancel_import_from_watson(qwatson_bot, newdir):
    """
    Test that the dialog to import settings and data from Watson the first
    time QWatson is started is working as expected when the import is
    cancelled by the user.
    """
    qwatson, qtbot, mocker = qwatson_bot(qwatson_dir=newdir)

    # Assert that the import dialog it shown on first start :

    assert qwatson.import_dialog is not None
    assert qwatson.import_dialog.isVisible()

    # Answer Cancel in the import dialog and assert that the frames and that
    # the activity input dialog is empty :

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


def test_import_from_watson_noshow(qwatson_bot, newdir):
    """
    Test that the import from watson dialog is not shown the second time
    QWatson is started, even if the user cancelled the imports.
    """
    qwatson, qtbot, mocker = qwatson_bot(qwatson_dir=newdir)

    # Assert that the import from Watson dialog is not shown on the second run.

    assert qwatson.import_dialog is None
    assert qwatson.currentIndex() == 0

    assert len(qwatson.client.frames) == 0
    for table in qwatson.overview_widg.table_widg.tables:
        assert table.view.proxy_model.get_accepted_row_count() == 0

    assert qwatson.currentProject() == ''
    assert qwatson.comment_manager.text() == ''
    assert qwatson.tag_manager.tags == []


def test_accept_import_from_watson(qwatson_bot, newdir):
    """
    Test that the dialog to import settings and data from Watson the first
    time QWatson is started is working as expected when the import is
    accepted by the user.
    """
    delete_folder_recursively(newdir, delroot=True)
    qwatson, qtbot, mocker = qwatson_bot(qwatson_dir=newdir)

    # Assert that the import dialog it shown.

    assert qwatson.import_dialog is not None
    assert qwatson.import_dialog.isVisible()

    # Answer 'Import' in the import dialog and assert that the frames and that
    # the activity input dialog data.

    with qtbot.waitSignal(qwatson.import_dialog.destroyed):
        qtbot.mouseClick(qwatson.import_dialog.buttons['Import'],
                         Qt.LeftButton)

    assert qwatson.import_dialog is None
    assert qwatson.currentIndex() == 0

    table = qwatson.overview_widg.table_widg.tables[0]
    assert table.view.proxy_model.get_accepted_row_count() == 1

    assert len(qwatson.client.frames) == 1
    assert qwatson.currentProject() == 'p1'
    assert qwatson.tag_manager.tags == ['tag1', 'tag2', 'tag3']
    assert qwatson.comment_manager.text() == 'First activity'

# ---- Test Close


def test_close_when_running(qwatson_bot, now):
    """
    Test that the dialog that ask the user what to do when closing QWatson
    while an activity is running is working as expected.
    """
    qwatson, qtbot, mocker = qwatson_bot(now=now.shift(hours=4))

    # Start an activity from last

    qwatson.btn_startfrom.setCurrentIndex(1)
    assert qwatson.startFrom() == 'last'

    qtbot.mouseClick(qwatson.stopwatch.buttons['start'], Qt.LeftButton)
    assert qwatson.currentIndex() == 0
    assert qwatson.client.is_started

    # Close QWatson and answer Cancel in the dialog.

    qwatson.close()
    assert qwatson.currentIndex() == 2
    assert qwatson.close_dial.isVisible()

    qtbot.mouseClick(qwatson.close_dial.buttons['Cancel'], Qt.LeftButton)
    assert qwatson.client.is_started
    assert qwatson.currentIndex() == 0
    assert qwatson.isVisible()
    assert not qwatson.close_dial.isVisible()
    assert len(qwatson.client.frames) == 1

    # Close QWatson and answer No in the dialog.

    qwatson.close()
    assert qwatson.currentIndex() == 2
    assert qwatson.close_dial.isVisible()

    qtbot.mouseClick(qwatson.close_dial.buttons['No'], Qt.LeftButton)
    assert not qwatson.client.is_started
    assert not qwatson.isVisible()
    assert len(qwatson.client.frames) == 1

    # Restart QWatson and start the tracker.

    qwatson.show()
    qtbot.waitForWindowShown(qwatson)
    qtbot.mouseClick(qwatson.stopwatch.buttons['start'], Qt.LeftButton)
    assert qwatson.currentIndex() == 0
    assert qwatson.client.is_started

    # Close QWatson and answer Yes in the dialog.

    qwatson.close()
    assert qwatson.currentIndex() == 2
    assert qwatson.close_dial.isVisible()

    qtbot.mouseClick(qwatson.close_dial.buttons['Yes'], Qt.LeftButton)
    assert not qwatson.client.is_started
    assert qwatson.currentIndex() == 0
    assert not qwatson.isVisible()

    frame = qwatson.client.frames[-1]
    assert len(qwatson.client.frames) == 2
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-07-30 07:25'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-07-30 11:25'


# ---- Test Show Overview Table


def test_show_overview_table(qwatson_bot, appdir):
    """
    Test that the overview table window is shown and focused as expected when
    clicking on the 'Activity Overview' button on the mainwindow.
    """
    qwatson, qtbot, mocker = qwatson_bot()
    overview = qwatson.overview_widg
    qtbot.addWidget(overview)

    qtbot.mouseClick(qwatson.btn_report, Qt.LeftButton)
    qtbot.waitForWindowShown(overview)
    assert overview.hasFocus()

    # Give focus to the main window, then click on the btn_report and assert
    # that the focus is given back to the overview window.

    qwatson.activateWindow()
    qwatson.raise_()
    qwatson.setFocus()

    assert not overview.hasFocus()
    qtbot.mouseClick(qwatson.btn_report, Qt.LeftButton)
    assert overview.hasFocus()

    # Minimize the overview window and restore it by clicking on btn_report.

    overview.showMinimized()
    assert overview.isMinimized()
    assert not overview.isActiveWindow()
    assert not overview.hasFocus()

    qtbot.mouseClick(qwatson.btn_report, Qt.LeftButton)
    assert overview.hasFocus()
    assert overview.isActiveWindow()

    # Maximize and minimize the overview window to the taskbar,
    # then restore it by clicking on btn_report.

    overview.showMaximized()
    overview.showMinimized()
    assert overview.isMaximized()
    assert overview.isMinimized()
    assert not overview.isActiveWindow()
    assert not overview.hasFocus()

    qtbot.mouseClick(qwatson.btn_report, Qt.LeftButton)
    assert overview.isMaximized()
    assert not overview.isMinimized()
    assert overview.isActiveWindow()
    assert overview.hasFocus()


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
