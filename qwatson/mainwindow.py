# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys
import platform
import os
import os.path as osp
import shutil
import json

# ---- Third parties imports

import click
import arrow
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWidgets import (QApplication, QGridLayout, QLabel, QLineEdit,
                             QSizePolicy, QWidget, QStackedWidget, QVBoxLayout)

# ---- Local imports

from qwatson.utils import icons
from qwatson.widgets.tags import TagLineEdit
from qwatson.watson_ext.watsonextends import Watson
from qwatson.watson_ext.watsonhelpers import (
    round_frame_at, reset_watson, get_frame_nbr_for_project)
from qwatson.widgets.projects import ProjectManager
from qwatson.widgets.clock import StopWatchWidget
from qwatson.widgets.tableviews import ActivityOverviewWidget
from qwatson.widgets.toolbar import (QToolButtonSmall, DropDownToolButton,
                                     HistoryNavigationWidget, ToolBarWidget)
from qwatson import __namever__
from qwatson.models.tablemodels import WatsonTableModel
from qwatson.dialogs import (ImportDialog, DateTimeInputDialog, CloseDialog,
                             DelProjectDialog, MergeProjectDialog)
from qwatson.widgets.layout import ColoredFrame

ROUNDMIN = {'round to 1min': 1, 'round to 5min': 5, 'round to 10min': 10}
STARTFROM = {'start from now': 'now', 'start from last': 'last',
             'start from other': 'other'}


class QWatsonProjectMixin(object):
    """
    A mixin for the main QWatson class with the necessary methods to handle
    the management of watson projects.
    """

    def setup_project_manager(self):
        """Setup the widget to manage projects in QWatson."""
        self.project_manager = ProjectManager(self.client)

        self.project_manager.sig_rename_project.connect(self.rename_project)
        self.project_manager.sig_add_project.connect(self.add_new_project)
        self.project_manager.sig_del_project.connect(self.del_project)
        self.project_manager.sig_project_changed.connect(self.project_changed)

        return self.project_manager

    def setup_del_project_dialog(self):
        """
        Setup the dialog to ask the user confirmation before deleting a
        project and its associated frames.
        """
        self.del_project_dialog = DelProjectDialog(main=self, parent=self)

    def setup_merge_project_dialog(self):
        """
        Setup the dialog to ask the user confirmation before merging a
        project with another.
        """
        self.merge_project_dialog = MergeProjectDialog(main=self, parent=self)

    def currentProject(self):
        """Return the currently selected project in the project manager."""
        return self.project_manager.currentProject()

    def setCurrentProject(self, poject):
        """Set the currently selected project in the project manager."""
        self.project_manager.setCurrentProject(poject)

    # ---- Handlers

    def project_changed(self, index):
        """Handle when the project selection change in the manager."""
        pass

    def rename_project(self, old_name, new_name, force=False):
        """
        Rename the project with the new provided name. An error will be
        raised if 'old_name' is not in the list of Watson.project.
        """
        if old_name == new_name:
            self.project_manager.setCurrentProject(new_name)
            return

        if force is True:
            self.model.beginResetModel()
            self.project_manager.model.beginResetModel()
            self.client.rename_project(old_name, new_name)
            self.model.endResetModel()
            self.project_manager.model.endResetModel()
            self.project_manager.setCurrentProject(new_name)
        elif force is False:
            na_old = get_frame_nbr_for_project(self.client, old_name)
            na_new = get_frame_nbr_for_project(self.client, new_name)
            if na_old > 0 and na_new > 0:
                # Since the project 'old_name' is not empty and the project
                # 'new_name' already exists and is not empty, we ask the
                # the user confirmation before merging all activities
                # of project 'old_name' with those of project 'new_name'.
                self.merge_project_dialog.show(
                    old_name, na_old, new_name, na_new)
            else:
                self.rename_project(old_name, new_name, force=True)

    def add_new_project(self, project):
        """Add the new project to the database."""
        if project not in self.client.projects:
            self.project_manager.model.beginResetModel()
            self.client.add_project(project)
            self.project_manager.model.endResetModel()
        self.project_manager.setCurrentProject(project)

    def del_project(self, project, force=False):
        """
        Ask for confirmation to delete the corresponding project from the
        database and update the model.

        If force is False, a dialog will ask the user before deleting the
        project.
        """
        if force is False:
            self.del_project_dialog.show(
                project, get_frame_nbr_for_project(self.client, project))
        elif force is True and project in self.client.projects:
            index = self.project_manager.currentProjectIndex()

            self.model.beginResetModel()
            self.project_manager.model.beginResetModel()
            self.client.delete_project(project)
            self.model.endResetModel()
            self.project_manager.model.endResetModel()

            index = min(index, len(self.client.projects)-1)
            self.project_manager.setCurrentProjectIndex(index)


class QWatsonImportMixin(object):
    """
    A mixin for the main QWatson class with the necessary methods to handle
    the import of config and data files from the watson application folder
    to that of QWatson.
    """

    def setup_import_dialog(self):
        """
        Setup a dialog to import data from the watson application folder
        to that of QWatson the first time QWatson is started.
        """
        if not osp.exists(self.client.frames_file):
            watson_frames_exists = osp.exists(osp.join(
                os.environ.get('WATSON_DIR') or click.get_app_dir('watson'),
                'frames'))
            if watson_frames_exists:
                self.import_dialog = ImportDialog(main=self, parent=self)
                self.import_dialog.show()
            else:
                self.create_empty_frames_file()
                self.import_dialog = None
        else:
            self.import_dialog = None

    def import_data_from_watson(self):
        """
        Copy the relevant resources files from the watson application folder
        to that of QWatson.
        """
        if not osp.exists(self.client._dir):
            os.makedirs(self.client._dir)

        filenames = ['frames', 'frames.bak', 'last_sync', 'state', 'state.bak']
        watson_dir = (os.environ.get('WATSON_DIR') or
                      click.get_app_dir('watson'))
        for filename in filenames:
            if osp.exists(osp.join(watson_dir, filename)):
                shutil.copyfile(osp.join(watson_dir, filename),
                                osp.join(self.client._dir, filename))
        self.reset_model_and_gui()

    def create_empty_frames_file(self):
        """
        Create an empty frame file to indicate that QWatson have been
        started at least one time.
        """
        if not osp.exists(self.client._dir):
            os.makedirs(self.client._dir)

        content = json.dumps({})
        with open(self.client.frames_file, 'w') as f:
            f.write(content)

    def reset_model_and_gui(self):
        """
        Force a reset of the watson client and a refresh of the gui and
        table model.
        """
        reset_watson(self.client)
        self.project_manager.model.modelReset.emit()
        self.model.modelReset.emit()
        if len(self.client.frames) > 0:
            lastframe = self.client.frames[-1]
            self.project_manager.setCurrentProject(lastframe.project)
            self.tag_manager.set_tags(lastframe.tags)
            self.comment_manager.setText(lastframe.message)


class QWatsonActivityMixin(object):
    """
    A mixin for the main QWatson class with the necessary methods to handle
    the management of watson activities.
    """

    def setup_activity_overview(self):
        """Setup the widget to show and edit activities."""
        self.overview_widg = ActivityOverviewWidget(self.model)
        self.overview_widg.sig_add_activity.connect(self.add_new_activity)

    def add_new_activity(self, index, start, stop):
        """
        Add a new activity in frames at index with the specified start and
        stop times.
        """
        self.model.beginInsertRows(QModelIndex(), index, index)
        self.model.client.insert(
            index, self.currentProject(), start, stop,
            tags=self.tag_manager.tags, message=self.comment_manager.text())
        self.model.client.save()
        self.model.endInsertRows()


class QWatson(QWidget, QWatsonImportMixin, QWatsonProjectMixin,
              QWatsonActivityMixin):

    def __init__(self, config_dir=None, parent=None):
        super(QWatson, self).__init__(parent)
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowTitle(__namever__)
        self.setMinimumWidth(300)
        self.setWindowFlags(Qt.Window |
                            Qt.WindowMinimizeButtonHint |
                            Qt.WindowCloseButtonHint)

        if platform.system() == 'Windows':
            import ctypes
            myappid = __namever__
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                myappid)

        config_dir = (config_dir or
                      os.environ.get('QWATSON_DIR') or
                      click.get_app_dir('QWatson'))

        self.client = Watson(config_dir=config_dir)
        self.model = WatsonTableModel(self.client)

        self.setup_activity_overview()
        self.setup()

        if self.client.is_started:
            self.add_new_project(self.client.current['project'])
            self.tag_manager.set_tags(['error'])
            self.comment_manager.setText("last session not closed correctly.")
            self.stop_watson()

    # ---- Setup layout

    def setup(self):
        """Setup the main widget."""

        # Setup the stack widget.

        self.stackwidget = QStackedWidget()

        self.setup_activity_tracker()
        self.setup_datetime_input_dialog()
        self.setup_close_dialog()
        self.setup_del_project_dialog()
        self.setup_merge_project_dialog()
        self.setup_import_dialog()

        # Setup the main layout of the widget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stackwidget)

    def setup_close_dialog(self):
        """
        Setup a dialog that is shown when closing QWatson while and activity
        is being tracked.
        """
        self.close_dial = CloseDialog(parent=self)
        self.close_dial.register_dialog_to(self)

    def setup_datetime_input_dialog(self):
        """
        Setup the dialog to ask the user to enter a datetime value for
        the starting time of the activity.
        """
        self.datetime_input_dial = DateTimeInputDialog(parent=self)
        self.datetime_input_dial.register_dialog_to(self)

    # ---- Main interface

    def setup_activity_tracker(self):
        """Setup the widget used to start, track, and stop new activity."""
        stopwatch = self.setup_stopwatch()
        managers = self.setup_watson_managers()
        statusbar = self.setup_statusbar()

        tracker = QWidget()
        layout = QVBoxLayout(tracker)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(stopwatch)
        layout.addWidget(managers)
        layout.addWidget(statusbar)
        layout.setStretch(1, 100)

        self.stackwidget.addWidget(tracker)

    def setup_watson_managers(self):
        """
        Setup the embedded dialog to setup the current activity parameters.
        """
        project_manager = self.setup_project_manager()

        self.tag_manager = TagLineEdit()
        self.tag_manager.setPlaceholderText("Tags (comma separated)")

        self.comment_manager = QLineEdit()
        self.comment_manager.setPlaceholderText("Comment")

        # ---- Setup the layout

        managers = ColoredFrame('light')

        layout = QGridLayout(managers)
        layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(project_manager, 0, 1)
        layout.addWidget(self.tag_manager, 1, 1)
        layout.addWidget(self.comment_manager, 2, 1)

        layout.addWidget(QLabel('project :'), 0, 0)
        layout.addWidget(QLabel('tags :'), 1, 0)
        layout.addWidget(QLabel('comment :'), 2, 0)

        # Set current activity inputs to the last ones saved in the database.
        if len(self.client.frames) > 0:
            project_manager.setCurrentProject(self.client.frames[-1][2])
            self.tag_manager.set_tags(self.client.frames[-1].tags)
            self.comment_manager.setText(self.client.frames[-1].message)

        return managers

    def setup_stopwatch(self):
        """
        Setup the widget that contains a button to start/stop Watson and a
        digital clock that shows the elapsed amount of time since Watson
        was started.
        """
        self.stopwatch = StopWatchWidget()
        self.stopwatch.sig_btn_start_clicked.connect(self.start_watson)
        self.stopwatch.sig_btn_stop_clicked.connect(self.stop_watson)
        self.stopwatch.sig_btn_cancel_clicked.connect(self.cancel_watson)

        return self.stopwatch

    def setup_statusbar(self):
        """Setup the toolbar located at the bottom of the main widget."""
        self.btn_report = QToolButtonSmall('note')
        self.btn_report.clicked.connect(self.overview_widg.show)
        self.btn_report.setToolTip(
            "<b>Activity Overview</b><br><br>"
            "Open the activity overview window.")

        self.round_time_btn = DropDownToolButton(style='text_only')
        self.round_time_btn.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.round_time_btn.addItems(list(ROUNDMIN.keys()))
        self.round_time_btn.setCurrentIndex(1)
        self.round_time_btn.setToolTip(
            "<b>Round Start and Stop</b><br><br>"
            "Round start and stop times to the nearest"
            " multiple of the selected factor.")

        self.btn_startfrom = DropDownToolButton(style='text_only')
        self.btn_startfrom.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.btn_startfrom.addItems(
            ['start from now', 'start from last', 'start from other'])
        self.btn_startfrom.setCurrentIndex(0)
        self.btn_startfrom.setToolTip(
            "<b>Start From</b><br><br>"
            "Set whether the current activity starts"
            " from the current time (now),"
            " from the stop time of the last logged activity (last),"
            " or from a user defined time (other).")

        # Setup the layout of the statusbar

        statusbar = ColoredFrame()
        statusbar.set_background_color('window')

        layout = QHBoxLayout(statusbar)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.round_time_btn)
        layout.addWidget(self.btn_startfrom)
        layout.addStretch(100)
        layout.addWidget(self.btn_report)

        return statusbar

    def roundTo(self):
        """
        Return the start and stop rounding time factor, in minutes, that
        corresponds to the option selected in the round_time_btn.
        """
        return ROUNDMIN[self.round_time_btn.text()]

    def startFrom(self):
        """
        Return the mode to use to determine at what reference time the activity
        must refer to calculate its elapsed time.
        """
        return STARTFROM[self.btn_startfrom.text()]

    # ---- Stackwidget handlers

    def addWidget(self, widget):
        """
        Add a widget to the stackwidget and return the index where the
        widget was added.
        """
        self.stackwidget.addWidget(widget)
        return self.stackwidget.count() - 1

    def removeWidget(self, widget):
        """Remove a widget from the stackwidget."""
        self.stackwidget.removeWidget(widget)

    def currentIndex(self):
        """Return the current index of the stackwidget."""
        return self.stackwidget.currentIndex()

    def setCurrentIndex(self, index):
        """Set the current index of the stackwidget."""
        self.stackwidget.setCurrentIndex(index)

    # ---- Toolbar handlers

    def start_watson(self, start_time=None):
        """Start monitoring a new activity with the Watson client."""
        if isinstance(start_time, arrow.Arrow):
            self.btn_startfrom.setEnabled(False)
            self.stopwatch.start(start_time)
            self.client.start(self.currentProject())
            self.client._current['start'] = start_time
        else:
            frames = self.client.frames
            if self.startFrom() == 'now':
                self.start_watson(arrow.now())
            elif self.startFrom() == 'last' and len(frames) > 0:
                self.start_watson(min(frames[-1].stop, arrow.now()))
            else:
                self.datetime_input_dial.show()

    def cancel_watson(self):
        """Cancel the Watson client if it is running and reset the UI."""
        self.btn_startfrom.setEnabled(True)
        self.stopwatch.cancel()
        if self.client.is_started:
            self.client.cancel()

    def stop_watson(self, message=None, project=None, tags=None,
                    round_to=None):
        """Stop Watson and update the table model."""
        self.btn_startfrom.setEnabled(True)
        self.stopwatch.stop()

        self.client._current['message'] = \
            self.comment_manager.text() if message is None else message
        self.client._current['project'] = \
            self.currentProject() if project is None else project
        self.client._current['tags'] = \
            self.tag_manager.tags if tags is None else tags

        self.model.beginInsertRows(
            QModelIndex(), len(self.client.frames), len(self.client.frames))
        self.client.stop()

        # Round the start and stop times of the last added frame.
        round_frame_at(self.client, -1,
                       self.roundTo() if round_to is None else round_to)

        self.client.save()
        self.model.endInsertRows()

    def closeEvent(self, event):
        """Qt method override."""
        if self.client.is_started:
            self.close_dial.show()
            event.ignore()
        else:
            self.overview_widg.close()
            self.client.save()
            event.accept()
            print("QWatson is closed.\n")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    watson_gui = QWatson()
    watson_gui.show()
    watson_gui.setFixedSize(watson_gui.size())
    print("QWatson is running...")
    sys.exit(app.exec_())
