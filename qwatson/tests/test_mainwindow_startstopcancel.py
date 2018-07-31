# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

"""
Test that starting, stopping and cancelling the monitoring of activities is
working as expected.
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
from qwatson.watson_ext.watsonhelpers import round_frame_at
from qwatson.utils.dates import (local_arrow_from_tuple, qdatetime_from_arrow,
                                 qdatetime_from_str)
from qwatson.utils.fileio import delete_folder_recursively


@pytest.fixture(scope="module")
def now():
    return local_arrow_from_tuple((2018, 7, 30, 7, 23, 44))


@pytest.fixture()
def appdir(now):
    # We do not use the tmpdir_factory fixture because we use the files
    # produces by the tests to test QWatson locally.

    appdir = osp.join(
        osp.dirname(__file__), 'appdir', 'mainwindow_startstopcancel')
    delete_folder_recursively(appdir)

    # Create the frames file.

    frames = [[now.shift(hours=-3).timestamp, now.timestamp, "p1",
               "e22fe653844442bab09a109f086688ec",
               ["tag1", "tag2", "tag3"], now.timestamp, "First activity"]]
    with open(osp.join(appdir, 'frames'), 'w') as f:
        f.write(json.dumps(frames))

    return appdir


@pytest.fixture
def qwatson_creator(qtbot, mocker, appdir, now):
    mocker.patch('arrow.now', return_value=now)
    mocker.patch('time.time', return_value=now.timestamp)
    qwatson = QWatson(config_dir=appdir)

    round_frame_at(qwatson.client, -1, 5)

    qtbot.addWidget(qwatson)
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    # Cancel the imports of data from Watson :

    if qwatson.import_dialog is not None:
        qtbot.mouseClick(qwatson.import_dialog.buttons['Cancel'],
                         Qt.LeftButton)

    yield qwatson, qtbot, mocker

    qwatson.close()


# ---- Test Init and Defaults


def test_init_and_defaults(qwatson_creator):
    """Test that the stopwatch widget is initialized as expected."""
    qwatson, qtbot, mocker = qwatson_creator
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


# ---- Test Start / Stop / Cancel


def test_startstop(qwatson_creator, now):
    """
    Test that starting and stoping the monitoring of an activity work
    as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator

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


def test_start_from_last(qwatson_creator, now):
    """
    Test that starting an activity with the option 'start from' set to 'last'
    works as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator

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


def test_start_from_last_when_later_than_now(qwatson_creator, now):
    """
    Test that starting a new activity with the option 'start from' set to
    'last' is working as expected when the stop time of the last saved
    activity is later than current time (See Issue #53 and PR #54).
    """
    qwatson, qtbot, mocker = qwatson_creator

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


def test_start_from_other(qwatson_creator, now):
    """
    Test that starting an activity with the option 'start from' set to 'other'
    works as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator
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


def test_startcancel(qwatson_creator, now):
    """
    Test that starting and cancelling the monitoring of an activity work
    as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator
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


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
