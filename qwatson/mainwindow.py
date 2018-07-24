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
from PyQt5.QtWidgets import (QApplication, QGridLayout, QHBoxLayout,
                             QLabel, QLineEdit, QSizePolicy, QWidget,
                             QStackedWidget, QVBoxLayout)

# ---- Local imports

from qwatson.utils import icons
from qwatson.managers.projects import ProjectManager
from qwatson.widgets.tags import TagLineEdit
from qwatson.watson.watsonextends import Watson
from qwatson.watson.watsonhelpers import round_frame_at, reset_watson
from qwatson.widgets.clock import ElapsedTimeLCDNumber
from qwatson.widgets.tableviews import WatsonOverviewWidget
from qwatson.widgets.toolbar import (
    OnOffToolButton, QToolButtonSmall, DropDownToolButton)
from qwatson import __namever__
from qwatson.models.tablemodels import WatsonTableModel
from qwatson.dialogs import ImportDialog, DateTimeInputDialog, CloseDialog
from qwatson.widgets.layout import ColoredFrame

ROUNDMIN = {'round to 1min': 1, 'round to 5min': 5, 'round to 10min': 10}
STARTFROM = {'start from now': 'now', 'start from last': 'last',
             'start from other': 'other'}


class QWatson(QWidget, QWatsonImportMixin):

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

        config_dir = config_dir or click.get_app_dir('QWatson')
        self.client = Watson(config_dir=config_dir)
        self.model = WatsonTableModel(self.client)

        if self.client.is_started:
            self.stop_watson(message="last session not closed correctly.",
                             tags=['error'])

        self.overview_widg = WatsonOverviewWidget(self.client, self.model)
        self.setup()

    # ---- Setup layout

    def setup(self):
        """Setup the main widget."""

        # Setup the stack widget.
        self.stackwidget = QStackedWidget()
        self.setup_activity_tracker()
        self.setup_datetime_input_dialog()
        self.setup_close_dialog()
        self.setup_import_dialog()

        # Setup the main layout of the widget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stackwidget)

    def setup_activity_tracker(self):
        """Setup the widget used to start, track, and stop new activity."""
        timebar = self.setup_timebar()
        managers = self.setup_watson_managers()
        statusbar = self.setup_statusbar()

        # ---- Setup the layout of the main widget

        tracker = QWidget()
        layout = QVBoxLayout(tracker)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(timebar)
        layout.addWidget(managers)
        layout.addWidget(statusbar)
        layout.setStretch(1, 100)

        self.stackwidget.addWidget(tracker)

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

    def setup_watson_managers(self):
        """
        Setup the embedded dialog to setup the current activity parameters.
        """
        self.project_manager = ProjectManager()

        self.project_manager.sig_project_added.connect(self.new_project_added)
        self.project_manager.sig_project_changed.connect(self.project_changed)
        self.project_manager.sig_project_removed.connect(self.project_removed)
        self.project_manager.sig_project_renamed.connect(self.project_renamed)
        self.project_manager.set_projects(self.client.projects)

        self.tag_manager = TagLineEdit()
        self.tag_manager.setPlaceholderText("Tags (comma separated)")

        self.comment_manager = QLineEdit()
        self.comment_manager.setPlaceholderText("Comment")

        # ---- Setup the layout

        managers = ColoredFrame('light')

        layout = QGridLayout(managers)
        layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(self.project_manager, 0, 1)
        layout.addWidget(self.tag_manager, 1, 1)
        layout.addWidget(self.comment_manager, 2, 1)

        layout.addWidget(QLabel('project :'), 0, 0)
        layout.addWidget(QLabel('tags :'), 1, 0)
        layout.addWidget(QLabel('comment :'), 2, 0)

        # Set current activity inputs to the last ones saved in the database.
        if len(self.client.frames) > 0:
            self.project_manager.set_current_project(self.client.frames[-1][2])
            self.tag_manager.set_tags(self.client.frames[-1].tags)
            self.comment_manager.setText(self.client.frames[-1].message)

        return managers

    def setup_timebar(self):
        """
        Setup the widget that contains a button to start/stop Watson and a
        digital clock that shows the elapsed amount of time since Watson
        was started.
        """
        self.btn_startstop = OnOffToolButton('process_start', 'process_stop')
        self.btn_startstop.setIconSize(icons.get_iconsize('large'))
        self.btn_startstop.setToolTip(
            "Start or stop monitoring time for the given project")
        self.btn_startstop.sig_value_changed.connect(
            self.btn_startstop_isclicked)

        self.elap_timer = ElapsedTimeLCDNumber()
        size_hint = self.elap_timer.sizeHint()
        size_ratio = size_hint.width()/size_hint.height()
        self.elap_timer.setFixedHeight(icons.get_iconsize('large').height())
        self.elap_timer.setMinimumWidth(self.elap_timer.height() * size_ratio)

        # ---- Setup layout

        timebar = ColoredFrame()
        timebar.set_background_color('window')

        layout = QGridLayout(timebar)
        layout.addWidget(self.btn_startstop, 0, 0)
        layout.addWidget(self.elap_timer, 0, 1)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setColumnStretch(2, 100)

        return timebar

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

        self.start_from = DropDownToolButton(style='text_only')
        self.start_from.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.start_from.addItems(
            ['start from now', 'start from last', 'start from other'])
        self.start_from.setCurrentIndex(0)
        self.start_from.setToolTip(
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
        layout.addWidget(self.start_from)
        layout.addStretch(100)
        layout.addWidget(self.btn_report)

        return statusbar

    # ---- Layout handlers

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

    # ---- Project handlers

    def project_changed(self, index):
        """Handle when the project selection change in the manager."""
        self.btn_startstop.setEnabled(index != -1)

    def project_renamed(self, old_name, new_name):
        """Handle when a project is renamed in the manager."""
        if old_name != new_name:
            self.model.beginResetModel()
            self.client.rename_project(old_name, new_name)
            self.model.endResetModel()

    def new_project_added(self, project):
        """Handle when a new project is added in the manager."""
        if project not in self.client.projects:
            self.client.add_project(project)

    def project_removed(self, project):
        """
        Handle when a project is removed from the manager by removing
        the corresponding project from the database and updating the model.
        """
        if project in self.client.projects:
            self.model.beginResetModel()
            self.client.delete_project(project)
            self.model.endResetModel()

    # ---- Toolbar handlers

    def btn_startstop_isclicked(self):
        """Handle when the button to start and stop Watson is clicked."""
        if self.btn_startstop.value():
            frames = self.client.frames
            start_from = STARTFROM[self.start_from.text()]
            if start_from == 'now':
                self.start_watson()
            elif start_from == 'last' and len(frames) > 0:
                self.start_watson(min(frames[-1].stop, arrow.now()))
            else:
                self.datetime_input_dial.show()
        else:
            self.elap_timer.stop()
            self.stop_watson(message=self.comment_manager.text(),
                             project=self.project_manager.current_project,
                             tags=self.tag_manager.tags,
                             round_to=ROUNDMIN[self.round_time_btn.text()])

    def start_watson(self, start_time=None):
        """Start monitoring a new activity with the Watson client."""
        self.client.start(self.project_manager.current_project)
        if start_time is not None:
            self.client._current['start'] = start_time
            self.elap_timer.start(start_time.timestamp)
        else:
            self.elap_timer.start()

    def cancel_watson(self):
        """Cancel the Watson client if it is running and reset the UI."""
        if self.client.is_started:
            self.client.cancel()
        self.btn_startstop.setValue(False, silent=True)

    def stop_watson(self, message=None, project=None, tags=None, round_to=5):
        """Stop Watson and update the table model."""
        if message is not None:
            self.client._current['message'] = message
        if project is not None:
            self.client._current['project'] = project
        if tags is not None:
            self.client._current['tags'] = tags

        self.model.beginInsertRows(
            QModelIndex(), len(self.client.frames), len(self.client.frames))
        self.client.stop()

        # Round the start and stop times of the last added frame.
        round_frame_at(self.client, -1, round_to)

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
