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

from qwatson.widgets.tableviews import QMessageBox
from qwatson.mainwindow import QWatson
from qwatson.utils.fileio import delete_folder_recursively
from qwatson.utils.dates import local_arrow_from_tuple


APPDIR = osp.join(osp.dirname(__file__), 'appdir')
NOW = local_arrow_from_tuple((2018, 6, 17, 0, 0, 0))
delete_folder_recursively(APPDIR)


@pytest.fixture
def qwatson_creator(qtbot, mocker):
    mocker.patch('arrow.now', return_value=NOW)
    qwatson = QWatson(config_dir=APPDIR)
    qtbot.addWidget(qwatson)
    return qwatson, qtbot, mocker


# ---- Test QWatsonProjectMixin

def test_add_project(qwatson_creator):
    """Test adding a new project."""
    qwatson, qtbot, mocker = qwatson_creator
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    assert qwatson.client.projects == ['']

    # Add a new project

    qtbot.mouseClick(qwatson.project_manager.btn_add, Qt.LeftButton)
    qtbot.keyClicks(qwatson.project_manager.project_cbox.linedit, 'p1')
    qtbot.keyPress(qwatson.project_manager.project_cbox.linedit, Qt.Key_Enter)

    assert qwatson.client.projects == ['', 'p1']
    assert qwatson.currentProject() == 'p1'

    # Add another new project

    qtbot.mouseClick(qwatson.project_manager.btn_add, Qt.LeftButton)
    qtbot.keyClicks(qwatson.project_manager.project_cbox.linedit, 'p2')
    qtbot.keyPress(qwatson.project_manager.project_cbox.linedit, Qt.Key_Enter)

    assert qwatson.client.projects == ['', 'p1', 'p2']
    assert qwatson.currentProject() == 'p2'


def test_add_activities(qwatson_creator):
    """Test adding new activities."""
    qwatson, qtbot, mocker = qwatson_creator
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    assert qwatson.client.projects == ['', 'p1', 'p2']
    assert qwatson.currentProject() == ''

    # Add some activities
    assert len(qwatson.client.frames) == 0
    for i, project in enumerate(['', '', 'p1', 'p1', 'p2']):
        qwatson.project_manager.setCurrentProject(project)
        assert qwatson.currentProject() == project

        # Start Watson.
        start = NOW.shift(hours=i)
        mocker.patch('arrow.now', return_value=start)
        qtbot.mouseClick(qwatson.btn_startstop, Qt.LeftButton)

        # Setup the comment.
        comment = 'Activity #%d' % i
        qwatson.comment_manager.clear()
        qtbot.keyClicks(qwatson.comment_manager, comment)
        qtbot.keyPress(qwatson.comment_manager, Qt.Key_Enter)
        assert qwatson.comment_manager.text() == comment

        # Stop Watson.
        stop = NOW.shift(hours=i+1)
        mocker.patch('arrow.now', return_value=stop)
        qtbot.mouseClick(qwatson.btn_startstop, Qt.LeftButton)
        assert qwatson.client.frames[-1].project == project
    assert len(qwatson.client.frames) == 5


def test_rename_project(qwatson_creator):
    """Test renaming a project."""
    qwatson, qtbot, mocker = qwatson_creator
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    assert qwatson.currentProject() == 'p2'
    qwatson.project_manager.setCurrentProject('')
    assert qwatson.currentProject() == ''

    qtbot.mouseClick(qwatson.project_manager.btn_rename, Qt.LeftButton)
    qtbot.keyClicks(qwatson.project_manager.project_cbox.linedit, 'p3')
    qtbot.keyPress(qwatson.project_manager.project_cbox.linedit, Qt.Key_Enter)
    assert qwatson.client.projects == ['', 'p1', 'p2', 'p3']
    assert qwatson.currentProject() == 'p3'
    assert qwatson.client.frames[0].project == 'p3'
    assert qwatson.client.frames[1].project == 'p3'
    assert qwatson.client.frames[2].project == 'p1'
    assert qwatson.client.frames[3].project == 'p1'
    assert qwatson.client.frames[4].project == 'p2'


def test_merge_project(qwatson_creator):
    """Test merging activities of two projects."""
    qwatson, qtbot, mocker = qwatson_creator
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    assert qwatson.currentProject() == 'p2'
    qwatson.project_manager.setCurrentProject('p3')
    assert qwatson.currentProject() == 'p3'

    qtbot.mouseClick(qwatson.project_manager.btn_rename, Qt.LeftButton)
    qtbot.keyClicks(qwatson.project_manager.project_cbox.linedit, 'p2')
    qtbot.keyPress(qwatson.project_manager.project_cbox.linedit, Qt.Key_Enter)
    assert qwatson.client.projects == ['', 'p1', 'p2']
    assert qwatson.currentProject() == 'p2'
    assert qwatson.client.frames[0].project == 'p2'
    assert qwatson.client.frames[1].project == 'p2'
    assert qwatson.client.frames[2].project == 'p1'
    assert qwatson.client.frames[3].project == 'p1'
    assert qwatson.client.frames[4].project == 'p2'


def test_del_project(qwatson_creator):
    """Test deleting a project."""
    qwatson, qtbot, mocker = qwatson_creator
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    assert qwatson.currentProject() == 'p2'

    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(qwatson.project_manager.btn_remove, Qt.LeftButton)
    assert qwatson.client.projects == ['', 'p1']
    assert len(qwatson.client.frames) == 2
    assert qwatson.client.frames[0].project == 'p1'
    assert qwatson.client.frames[1].project == 'p1'


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
