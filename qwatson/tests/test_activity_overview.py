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
from PyQt5.QtWidgets import QMessageBox

# ---- Local imports

from qwatson.watson_ext.watsonextends import Frames
from qwatson.mainwindow import QWatson
from qwatson.utils.dates import local_arrow_from_tuple
from qwatson.utils.fileio import delete_folder_recursively
from qwatson.utils.dates import qdatetime_from_str
from qwatson.models.delegates import (DateTimeDelegate, LineEditDelegate,
                                      TagEditDelegate, ToolButtonDelegate)


# ---- Fixtures and utilities


@pytest.fixture(scope="module")
def now():
    return local_arrow_from_tuple((2018, 6, 17, 23, 59, 0))


@pytest.fixture(scope="module")
def span(now):
    return now.floor('week').span('week')


@pytest.fixture
def appdir(now, span, tmpdir):
    """Temporary app directory fixture that also creates a test Frame file."""

    appdir = osp.join(str(tmpdir), 'appdir')

    delete_folder_recursively(appdir)
    if not osp.exists(appdir):
        os.makedirs(appdir)

    # Create the frames file.

    frames = Frames()
    i = 1
    while True:
        frame = frames.add(project='p%d' % (i//2),
                           start=span[0].shift(hours=i*6).timestamp,
                           stop=span[0].shift(hours=(i+1)*6).timestamp,
                           message='activity #%d' % (i//2),
                           tags=['CI', 'test', '#%d' % (i//2)],
                           updated_at=now
                           )
        if frame.stop >= span[1]:
            break
        i += 2

    with open(osp.join(appdir, 'frames'), 'w') as f:
        f.write(json.dumps(frames.dump(), indent=1, ensure_ascii=False))

    return appdir


@pytest.fixture
def qwatson(qtbot, mocker, appdir, now):
    """
    QWatson application fixture.
    """
    mocker.patch('arrow.now', return_value=now)
    qwatson = QWatson(config_dir=appdir)

    qtbot.addWidget(qwatson)
    qwatson.show()
    qtbot.waitForWindowShown(qwatson)

    qtbot.addWidget(qwatson.overview_widg)
    qtbot.mouseClick(qwatson.btn_report, Qt.LeftButton)
    qtbot.waitForWindowShown(qwatson.overview_widg)

    return qwatson


# ---- Tests


def test_overview_init(qwatson, span):
    """Test that the overview is initialized correctly."""
    overview = qwatson.overview_widg

    assert overview.isVisible()
    assert overview.table_widg.total_seconds == 7*(2*6)*60*60
    assert len(overview.table_widg.tables) == 7
    assert overview.table_widg.last_focused_table is None
    assert overview.table_widg.date_span == span

    # Assert that the overview table is showing the right number of activities.
    assert overview.table_widg.get_row_count() == [2, 2, 2, 2, 2, 2, 2]

    # Test that the tag and project filters are all checked.
    for item, action in overview.filter_btn.projects_menu._actions.items():
        assert action.defaultWidget().isChecked()

    for item, action in overview.filter_btn.tags_menu._actions.items():
        assert action.defaultWidget().isChecked()


def test_overview_row_selection(qwatson, qtbot):
    """
    Test that table and row selection is working as expected.
    """
    overview = qwatson.overview_widg
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


def test_mouse_hovered_row(qwatson, qtbot):
    """
    Test that the highlighting of mouse hovered row is working as expected.
    """
    overview = qwatson.overview_widg
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


@pytest.mark.parametrize("attr", ['projects_menu', 'tags_menu'])
def test_select_all_filter(qwatson, attr):
    """Test checking/unchecking all project and tag filters at once."""
    overview = qwatson.overview_widg
    menu = getattr(overview.filter_btn, attr)

    # Uncheck (Select All).
    menu._actions['__select_all__'].defaultWidget().setChecked(False)
    for item, action in menu._actions.items():
        assert not action.defaultWidget().isChecked()
    assert menu.checked_items() == []
    assert overview.table_widg.get_row_count() == [0, 0, 0, 0, 0, 0, 0]
    assert overview.table_widg.total_seconds == 0

    # Check (Select All).
    menu._actions['__select_all__'].defaultWidget().setChecked(True)
    for item, action in menu._actions.items():
        assert action.defaultWidget().isChecked()
    assert overview.table_widg.get_row_count() == [2, 2, 2, 2, 2, 2, 2]
    assert overview.table_widg.total_seconds == 7*(2*6)*60*60


def test_filter_activities(qwatson):
    """Test filtering activities by projects and tags."""
    overview = qwatson.overview_widg
    projects_menu = overview.filter_btn.projects_menu
    tags_menu = overview.filter_btn.tags_menu

    # Uncheck the (Select All) in the projects and tags menu.
    projects_menu._actions['__select_all__'].defaultWidget().setChecked(False)
    tags_menu._actions['__select_all__'].defaultWidget().setChecked(False)

    # Check some projects.
    checked_projects = ['p0', 'p1', 'p4', 'p6', 'p7']
    for project in checked_projects:
        projects_menu._actions[project].defaultWidget().setChecked(True)

    # Check some tags.
    # Note that the activity associated with the tag '#10' won't be shown
    # because its associated project is not checked.
    checked_tags = ['#0', '#1', '#6', '#10']
    for tag in checked_tags:
        tags_menu._actions[tag].defaultWidget().setChecked(True)

    assert overview.table_widg.get_row_count() == [2, 0, 0, 1, 0, 0, 0]
    assert projects_menu.checked_items() == ['p0', 'p1', 'p4', 'p6', 'p7']
    assert tags_menu.checked_items() == ['#0', '#1', '#10', '#6']
    assert overview.table_widg.total_seconds == 3*(6*60*60)

    # Check tag 'test'.
    tags_menu._actions['test'].defaultWidget().setChecked(True)
    assert overview.table_widg.get_row_count() == [2, 0, 1, 2, 0, 0, 0]
    assert tags_menu.checked_items() == ['#0', '#1', '#10', '#6', 'test']
    assert overview.table_widg.total_seconds == 5*(6*60*60)


def test_filter_no_tags_or_project(qwatson):
    """Test that activities without tag or project are shown in the table."""
    overview = qwatson.overview_widg
    projects_menu = overview.filter_btn.projects_menu
    tags_menu = overview.filter_btn.tags_menu

    # Remove all the tags of the first frame.
    assert qwatson.client.frames[0].tags == ['CI', 'test', '#0']
    index = qwatson.model.index(0, qwatson.model.COLUMNS['tags'])
    qwatson.model.editFrame(index, tags=[])
    assert qwatson.client.frames[0].tags == []

    assert overview.table_widg.total_seconds == (14*6) * (60*60)
    assert overview.table_widg.get_row_count() == [2, 2, 2, 2, 2, 2, 2]

    # Set the project of the second frame to ''.
    assert qwatson.client.frames[1].project == 'p1'
    index = qwatson.model.index(1, qwatson.model.COLUMNS['project'])
    qwatson.model.editFrame(index, project='')
    assert qwatson.client.frames[1].project == ''

    assert overview.table_widg.total_seconds == (14*6) * (60*60)
    assert overview.table_widg.get_row_count() == [2, 2, 2, 2, 2, 2, 2]

    # Uncheck the '' item in the projects and tags filter menu.
    projects_menu._actions[''].defaultWidget().setChecked(False)
    tags_menu._actions[''].defaultWidget().setChecked(False)

    assert overview.table_widg.total_seconds == (12*6) * (60*60)
    assert overview.table_widg.get_row_count() == [0, 2, 2, 2, 2, 2, 2]


def test_daterange_navigation(qwatson, span, qtbot):
    """
    Test that the widget to change the datespan of the activity overview is
    working as expected.
    """
    overview = qwatson.overview_widg
    assert not overview.date_range_nav.btn_next.isEnabled()

    # Move back one week.

    qtbot.mouseClick(overview.date_range_nav.btn_prev, Qt.LeftButton)
    new_span = (span[0].shift(weeks=-1), span[1].shift(weeks=-1))
    assert overview.table_widg.date_span == new_span
    assert overview.date_range_nav.btn_next.isEnabled()

    # Move back two additional weeks.

    qtbot.mouseClick(overview.date_range_nav.btn_prev, Qt.LeftButton)
    qtbot.mouseClick(overview.date_range_nav.btn_prev, Qt.LeftButton)
    new_span = (new_span[0].shift(weeks=-2), new_span[1].shift(weeks=-2))
    assert overview.table_widg.date_span == new_span
    assert overview.date_range_nav.btn_next.isEnabled()

    # Move forth one week.

    qtbot.mouseClick(overview.date_range_nav.btn_next, Qt.LeftButton)
    new_span = (new_span[0].shift(weeks=1), new_span[1].shift(weeks=1))
    assert overview.table_widg.date_span == new_span
    assert overview.date_range_nav.btn_next.isEnabled()

    # Go back home.

    qtbot.mouseClick(overview.date_range_nav.btn_home, Qt.LeftButton)
    assert overview.table_widg.date_span == span
    assert not overview.date_range_nav.btn_next.isEnabled()


def test_selected_row_is_cleared_when_navigating(qwatson, qtbot):
    """
    Test that the selected row is cleared when changing the date span of the
    overview table with the date range navigator widget.
    """
    overview = qwatson.overview_widg
    table = overview.table_widg.tables[1]

    # Select the second row of the second table.

    visual_rect = table.view.visualRect(table.view.proxy_model.index(1, 0))
    qtbot.mouseClick(
        table.view.viewport(), Qt.LeftButton, pos=visual_rect.center())
    assert table.get_selected_row() == 1
    assert overview.table_widg.last_focused_table == table

    # Move back and forth one week in the date range navigation widget.

    qtbot.mouseClick(overview.date_range_nav.btn_prev, Qt.LeftButton)

    # Assert that the selected row was cleared as expected.

    assert overview.table_widg.last_focused_table is None
    for table in overview.table_widg.tables:
        assert table.get_selected_row() is None


def test_import_frame_settings_to_mainwindow(qwatson, qtbot):
    """
    Test that copying over the selected frame data to the mainwindow is
    working as expected.
    """
    overview = qwatson.overview_widg

    assert qwatson.currentProject() == 'p13'
    assert qwatson.tag_manager.tags == ['#13', 'CI', 'test']
    assert qwatson.comment_manager.text() == 'activity #13'

    overview = qwatson.overview_widg
    qtbot.mouseClick(qwatson.btn_report, Qt.LeftButton)
    qtbot.waitForWindowShown(overview)
    assert overview.hasFocus()

    # Click on the btn to copy over selected frame data to mainwindow when no
    # frame is selected.

    assert overview.table_widg.last_focused_table is None
    qtbot.mouseClick(overview.btn_load_row_settings, Qt.LeftButton)

    assert qwatson.currentProject() == 'p13'
    assert qwatson.tag_manager.tags == ['#13', 'CI', 'test']
    assert qwatson.comment_manager.text() == 'activity #13'

    # Select the second row of the second table.

    table = overview.table_widg.tables[1]
    visual_rect = table.view.visualRect(table.view.proxy_model.index(1, 0))
    qtbot.mouseClick(
        table.view.viewport(), Qt.LeftButton, pos=visual_rect.center())
    assert table.get_selected_row() == 1
    assert overview.table_widg.last_focused_table == table

    # Click to copy over selected frame data to mainwindow.

    qtbot.mouseClick(overview.btn_load_row_settings, Qt.LeftButton)

    assert qwatson.currentProject() == 'p3'
    assert qwatson.tag_manager.tags == ['#3', 'CI', 'test']
    assert qwatson.comment_manager.text() == 'activity #3'


# ---- Test Edits


def test_edit_start_datetime(qwatson, qtbot):
    """Test editing the start date in the activity overview table."""
    overview = qwatson.overview_widg

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


def test_edit_stop_datetime(qwatson, qtbot):
    """Test editing the stop date in the activity overview table."""
    overview = qwatson.overview_widg

    # Edit the stop date of the first frame of the third table

    table = overview.table_widg.tables[2]
    index = table.view.proxy_model.index(0, 1)
    delegate = table.view.itemDelegate(table.view.proxy_model.index(0, 1))
    assert isinstance(delegate, DateTimeDelegate)

    # Check that the stop value is constraint by the start value of the frame

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


def test_edit_comment(qwatson, qtbot):
    """
    Test editing the comment in the activity overview table.
    """
    overview = qwatson.overview_widg

    # Edit the comment of the second entry in the fourth table :

    table = overview.table_widg.tables[3]
    col = table.view.proxy_model.sourceModel().COLUMNS['comment']
    index = table.view.proxy_model.index(1, col)

    frame = table.view.proxy_model.get_frame_from_index(index)
    assert frame.message == 'activity #7'

    # Edit the frame comment in the overview table :

    delegate = table.view.itemDelegate(index)
    table.view.edit(index)
    assert isinstance(delegate, LineEditDelegate)
    assert delegate.editor.text() == 'activity #7'

    # Enter a new comment for the activity.

    qtbot.keyClicks(delegate.editor, 'activity #7 (edited)')
    with qtbot.waitSignal(table.view.proxy_model.sig_sourcemodel_changed):
        qtbot.keyPress(delegate.editor, Qt.Key_Enter)

    frame = table.view.proxy_model.get_frame_from_index(index)
    assert frame.message == 'activity #7 (edited)'
    assert index.data() == 'activity #7 (edited)'


def test_edit_tags(qwatson, qtbot):
    """Test editing the tags in the activity overview table."""
    overview = qwatson.overview_widg

    # We will test this on the first entry of the fifth table :

    table = overview.table_widg.tables[4]
    col = table.view.proxy_model.sourceModel().COLUMNS['tags']
    index = table.view.proxy_model.index(0, col)

    frame = table.view.proxy_model.get_frame_from_index(index)
    assert frame.message == 'activity #8'
    assert frame.tags == ['CI', 'test', '#8']
    assert index.data() == '[CI] [test] [#8]'

    # Start editing the tags in the overview table :

    delegate = table.view.itemDelegate(index)
    table.view.edit(index)
    assert isinstance(delegate, TagEditDelegate)
    assert delegate.editor.tags == ['#8', 'CI', 'test']
    assert delegate.editor.text() == 'CI, test, #8'

    # Enter a new list of tags for the activity :

    qtbot.keyClicks(delegate.editor, 'tag1,tag3,  tag2')
    with qtbot.waitSignal(table.view.proxy_model.sig_sourcemodel_changed):
        qtbot.keyPress(delegate.editor, Qt.Key_Enter)

    frame = table.view.proxy_model.get_frame_from_index(index)
    assert frame.tags == ['tag1', 'tag2', 'tag3']
    assert index.data() == '[tag1] [tag2] [tag3]'


def test_delete_frame_no(qwatson, qtbot, mocker):
    """
    Test that deleting a frame from the activity overview, but answering no
    works correctly.
    """
    overview = qwatson.overview_widg

    # We will test this on the last entry of the last table :

    table = overview.table_widg.tables[-1]
    col = table.view.proxy_model.sourceModel().COLUMNS['icons']
    index = table.view.proxy_model.index(1, col)

    frame = table.view.proxy_model.get_frame_from_index(index)
    assert frame.message == 'activity #13'
    assert isinstance(table.view.itemDelegate(index), ToolButtonDelegate)

    # Click to delete last frame and answer No :

    visual_rect = table.view.visualRect(index)

    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.No)
    qtbot.mouseClick(table.view.viewport(), Qt.LeftButton,
                     pos=visual_rect.center())

    assert table.rowCount() == 2
    assert overview.table_widg.last_focused_table == table
    assert table.get_selected_row() is None
    assert len(overview.model.client.frames) == 14
    assert overview.model.client.frames[-1].message == 'activity #13'


def test_delete_frame_yes(qwatson, qtbot, mocker):
    """
    Test that deleting a frame from the activity overview, but answering no
    works correctly.
    """
    overview = qwatson.overview_widg

    # We will test this on the last entry of the last table :

    table = overview.table_widg.tables[-1]

    # Select the last row of the last table :

    visual_rect = table.view.visualRect(table.view.proxy_model.index(1, 0))
    qtbot.mouseClick(
        table.view.viewport(), Qt.LeftButton, pos=visual_rect.center())

    assert overview.table_widg.last_focused_table == table
    assert table.get_selected_row() == 1
    assert table.rowCount() == 2

    # Click to delete the second frame of the last table and answer Yes :

    col = table.view.proxy_model.sourceModel().COLUMNS['icons']
    visual_rect = table.view.visualRect(table.view.proxy_model.index(1, col))

    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(table.view.viewport(), Qt.LeftButton,
                     pos=visual_rect.center())

    assert table.rowCount() == 1
    assert overview.table_widg.last_focused_table == table
    assert table.get_selected_row() == 0
    assert len(overview.model.client.frames) == 13
    assert overview.model.client.frames[-1].message == 'activity #12'

    # Click to delete the last frame of the last table and answer Yes :

    visual_rect = table.view.visualRect(table.view.proxy_model.index(0, col))

    mocker.patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes)
    qtbot.mouseClick(
        table.view.viewport(), Qt.LeftButton, pos=visual_rect.center())

    assert overview.table_widg.last_focused_table is None
    assert table.get_selected_row() is None
    assert table.rowCount() == 0


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
