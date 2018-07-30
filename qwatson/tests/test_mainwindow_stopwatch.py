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
from qwatson.utils.dates import local_arrow_from_tuple
from qwatson.utils.fileio import delete_folder_recursively


@pytest.fixture(scope="module")
def appdir(tmpdir_factory):
    # We do not use the tmpdir_factory fixture because we use the files
    # produces by the tests to test QWatson locally.

    appdir = osp.join(
        osp.dirname(__file__), 'appdir', 'mainwindow_stopwatch')

    delete_folder_recursively(appdir)
    if not osp.exists(appdir):
        os.makedirs(appdir)

    # Create the projects file.

    with open(osp.join(appdir, 'projects'), 'w') as f:
        f.write(json.dumps(['p1']))

    return appdir


@pytest.fixture(scope="module")
def now():
    return local_arrow_from_tuple((2018, 7, 30, 7, 23, 44))


@pytest.fixture
def qwatson_creator(qtbot, mocker, appdir, now):
    mocker.patch('arrow.now', return_value=now)
    mocker.patch('time.time', return_value=now.timestamp)
    qwatson = QWatson(config_dir=appdir)

    qtbot.addWidget(qwatson)
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    # Cancel the imports of data from Watson :

    if qwatson.import_dialog is not None:
        qtbot.mouseClick(qwatson.import_dialog.buttons['Cancel'],
                         Qt.LeftButton)

    yield qwatson, qtbot, mocker

    qwatson.close()


# ---- Tests


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


def test_startstop(qwatson_creator, now):
    """
    Test that starting and stoping the monitoring of an activity work
    as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator
    stopwatch = qwatson.stopwatch

    # Start monitoring an activity.

    qtbot.mouseClick(stopwatch.buttons['start'], Qt.LeftButton)
    assert not stopwatch.buttons['start'].isEnabled()
    assert stopwatch.buttons['stop'].isEnabled()
    assert stopwatch.buttons['cancel'].isEnabled()
    assert stopwatch.isRunning() is True
    assert stopwatch.elap_timer._elapsed_time == 0

    # Setup project, tags, and comment.

    qwatson.setCurrentProject('p1')
    qwatson.tag_manager.set_tags(['test', 'start', 'stop'])
    qwatson.comment_manager.setText('Test start-stop')

    # Stop monitoring the activity.

    mocker.patch('arrow.now', return_value=now.shift(hours=3))
    mocker.patch('time.time', return_value=arrow.now().timestamp)
    qtbot.wait(11)
    assert stopwatch.elap_timer._elapsed_time == 3*60*60

    qtbot.mouseClick(stopwatch.buttons['stop'], Qt.LeftButton)
    assert stopwatch.buttons['start'].isEnabled()
    assert not stopwatch.buttons['stop'].isEnabled()
    assert not stopwatch.buttons['cancel'].isEnabled()
    assert stopwatch.isRunning() is False
    assert stopwatch.elap_timer._elapsed_time == 3*60*60

    assert len(qwatson.client.frames) == 1
    frame = qwatson.client.frames[-1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-07-30 07:25'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-07-30 10:25'
    assert frame.message == 'Test start-stop'
    assert frame.tags == ['start', 'stop', 'test']
    assert frame.project == 'p1'


def test_startcancel(qwatson_creator, now):
    """
    Test that starting and cancelling the monitoring of an activity work
    as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator
    stopwatch = qwatson.stopwatch

    # Start monitoring an activity.

    qtbot.mouseClick(stopwatch.buttons['start'], Qt.LeftButton)

    # There is no need to assert anything here since this was covered in the
    # previous test above.

    # Cancel monitoring the activity.

    mocker.patch('arrow.now', return_value=now.shift(hours=3))
    mocker.patch('time.time', return_value=arrow.now().timestamp)
    qtbot.wait(11)
    assert stopwatch.elap_timer._elapsed_time == 3*60*60

    qtbot.mouseClick(stopwatch.buttons['cancel'], Qt.LeftButton)
    assert stopwatch.buttons['start'].isEnabled()
    assert not stopwatch.buttons['stop'].isEnabled()
    assert not stopwatch.buttons['cancel'].isEnabled()
    assert stopwatch.isRunning() is False
    assert stopwatch.elap_timer._elapsed_time == 0

    assert len(qwatson.client.frames) == 1


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
