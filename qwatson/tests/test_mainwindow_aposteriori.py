# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

"""
Test that adding activities aposteriori from the activity overview widget is
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


# ---- Fixtures


@pytest.fixture(scope="module")
def now():
    return local_arrow_from_tuple((2018, 7, 25, 6, 0, 0))


@pytest.fixture(scope="module")
def appdir(now):
    # We do not use the tmpdir_factory fixture because we use the files
    # produces by the tests to test QWatson locally.

    appdir = osp.join(
        osp.dirname(__file__), 'appdir', 'mainwindow_aposteriori')

    delete_folder_recursively(appdir)
    if not osp.exists(appdir):
        os.makedirs(appdir)

    # Create the projects file.

    with open(osp.join(appdir, 'projects'), 'w') as f:
        f.write(json.dumps(['p1', 'p2', 'p3']))

    # Create the frames file.

    frames = [[now.timestamp, now.timestamp, "p1",
               "e22fe653844442bab09a109f086688ec",
               ["tag1", "tag2", "tag3"], now.timestamp, "Base activity"]]
    with open(osp.join(appdir, 'frames'), 'w') as f:
        f.write(json.dumps(frames))

    return appdir


@pytest.fixture
def qwatson_creator(qtbot, mocker, appdir, now):
    mocker.patch('arrow.now', return_value=now)
    qwatson = QWatson(config_dir=appdir)

    qtbot.addWidget(qwatson)
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    qtbot.addWidget(qwatson.overview_widg)
    qtbot.mouseClick(qwatson.btn_report, Qt.LeftButton)
    qtbot.waitForWindowShown(qwatson.overview_widg)

    yield qwatson, qtbot, mocker

    qwatson.close()


# ---- Tests


def test_setup(qwatson_creator):
    """Test that the projects and frames files were generated correctly."""
    qwatson, qtbot, mocker = qwatson_creator

    assert qwatson.client.projects == ['', 'p1', 'p2', 'p3']
    assert len(qwatson.client.frames) == 1
    assert qwatson.currentProject() == 'p1'
    assert qwatson.tag_manager.tags == ['tag1', 'tag2', 'tag3']
    assert qwatson.comment_manager.text() == 'Base activity'

    overview = qwatson.overview_widg
    assert overview.hasFocus()
    assert overview.table_widg.last_focused_table is None

    row_counts = [table.rowCount() for table in overview.table_widg.tables]
    assert row_counts == [0, 0, 1, 0, 0, 0, 0]


def test_add_activity_below_nofocus(qwatson_creator):
    """
    Test that adding an activity below when no row is selected in the overview
    table works as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator
    overview = qwatson.overview_widg

    qwatson.comment_manager.setText('Add activity below when no selected row.')
    qtbot.mouseClick(overview.add_act_below_btn, Qt.LeftButton)

    # Assert the that the frame was added correctly at the beginning of the
    # last day of the week with the right project and comment.

    assert len(qwatson.client.frames) == 2
    frame = qwatson.client.frames[1]
    assert frame.start == frame.stop == arrow.now().floor('week').shift(days=6)
    assert frame.project == 'p1'
    assert frame.message == 'Add activity below when no selected row.'
    assert frame.tags == ['tag1', 'tag2', 'tag3']

    # Assert that the overview table is showing the right thing.

    row_counts = [table.rowCount() for table in overview.table_widg.tables]
    assert row_counts == [0, 0, 1, 0, 0, 0, 1]


def test_add_activity_above_nofocus(qwatson_creator):
    """
    Test that adding an activity above when no row is selected in the overview
    table works as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator
    overview = qwatson.overview_widg

    qwatson.comment_manager.setText('Add activity above when no selected row.')
    qwatson.setCurrentProject('p2')
    qtbot.mouseClick(overview.add_act_above_btn, Qt.LeftButton)

    # Assert the that the frame was added correctly at the beginning of the
    # first day of the week with the right project and comment.

    assert len(qwatson.client.frames) == 3
    frame = qwatson.client.frames[0]
    assert frame.start == frame.stop == arrow.now().floor('week')
    assert frame.project == 'p2'
    assert frame.message == 'Add activity above when no selected row.'

    # Assert that the overview table is showing the right thing.

    row_counts = [table.rowCount() for table in overview.table_widg.tables]
    assert row_counts == [1, 0, 1, 0, 0, 0, 1]


def test_add_activity_above_selection(qwatson_creator):
    """
    Test that adding an activity above the selected row in the overview table
    works as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator
    overview = qwatson.overview_widg

    qwatson.setCurrentProject('p3')
    qwatson.comment_manager.setText('Add activity above selection')

    # Select the base activity and add a new activity above it.

    table = overview.table_widg.tables[2]
    visual_rect = table.view.visualRect(table.view.proxy_model.index(1, 0))
    qtbot.mouseClick(
        table.view.viewport(), Qt.LeftButton, pos=visual_rect.center())

    # Add an activity above the selection.

    qtbot.mouseClick(overview.add_act_above_btn, Qt.LeftButton)

    # Assert the that the frame was added correctly at the right index.

    assert len(qwatson.client.frames) == 4
    frame = qwatson.client.frames[1]
    assert frame.start == frame.stop == arrow.now()
    assert frame.project == 'p3'
    assert frame.message == 'Add activity above selection'

    # Assert that the overview table is showing the right number of activities
    # and that the base activity is still selected.

    row_counts = [table.rowCount() for table in overview.table_widg.tables]
    assert row_counts == [1, 0, 2, 0, 0, 0, 1]
    assert table.get_selected_row() == 1
    assert overview.table_widg.last_focused_table == table


def test_add_activity_below_selection(qwatson_creator):
    """
    Test that adding an activity below the selected row in the overview table
    works as expected.
    """
    qwatson, qtbot, mocker = qwatson_creator
    overview = qwatson.overview_widg

    qwatson.setCurrentProject('')
    qwatson.comment_manager.setText('Add activity below selection')

    # Select the base activity and add a new activity below. Note that an
    # activity has been added above the base activity.

    table = overview.table_widg.tables[2]
    visual_rect = table.view.visualRect(table.view.proxy_model.index(1, 0))
    qtbot.mouseClick(
        table.view.viewport(), Qt.LeftButton, pos=visual_rect.center())

    # Add an activity below the selection.

    qtbot.mouseClick(overview.add_act_below_btn, Qt.LeftButton)

    # Assert the that the frame was added correctly at the right index.

    assert len(qwatson.client.frames) == 5
    frame = qwatson.client.frames[3]
    assert frame.start == frame.stop == arrow.now()
    assert frame.project == ''
    assert frame.message == 'Add activity below selection'

    # Assert that the overview table is showing the right number of activities
    # and that the base activity is still selected.

    row_counts = [table.rowCount() for table in overview.table_widg.tables]
    assert row_counts == [1, 0, 3, 0, 0, 0, 1]
    assert table.get_selected_row() == 1
    assert overview.table_widg.last_focused_table == table


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
