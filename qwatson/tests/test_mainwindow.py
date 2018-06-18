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
from datetime import datetime

# ---- Third party imports

import pytest
from PyQt5.QtCore import Qt
import arrow

# ---- Local imports

from qwatson.mainwindow import QWatson
from qwatson.utils.fileio import delete_file_safely


WORKDIR = osp.dirname(__file__)


# Test MainWindow
# -------------------------------

def test_mainwindow_init(qtbot):
    """
    Test that the QWatson main widget and avtivity overview widgets are
    started correctly.
    """
    frames_file = osp.join(WORKDIR, 'frames')
    delete_file_safely(frames_file)
    delete_file_safely(frames_file + '.bak')
    qtbot.waitUntil(lambda: not osp.exists(frames_file))

    mainwindow = QWatson(WORKDIR)
    qtbot.addWidget(mainwindow)
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

    # ---- Check default

    activity_input_dial = mainwindow.activity_input_dial
    assert activity_input_dial.project == ''
    assert activity_input_dial.tags == []
    assert activity_input_dial.comment == ''
    assert mainwindow.round_time_btn.text() == 'round to 5min'

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
    start = arrow.get(datetime(2018, 6, 14, 15, 59, 54))
    mocker.patch('arrow.now', return_value=start)
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert mainwindow.elap_timer.is_started

    # Stop the activity timer
    stop = arrow.get(datetime(2018, 6, 14, 17, 12, 35))
    mocker.patch('arrow.now', return_value=stop)
    qtbot.mouseClick(mainwindow.btn_startstop, Qt.LeftButton)
    assert not mainwindow.elap_timer.is_started

    # Assert frame logged data

    assert len(mainwindow.client.frames) == 1
    frame = mainwindow.client.frames[0]
    assert frame.start == arrow.get(datetime(2018, 6, 14, 16, 0))
    assert frame.stop == arrow.get(datetime(2018, 6, 14, 17, 15))
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


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
