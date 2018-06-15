# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys
import platform
import os.path as osp

# ---- Third parties imports

from PyQt5.QtCore import (Qt, QModelIndex)
from PyQt5.QtWidgets import (QApplication, QGridLayout, QSizePolicy, QWidget)

# ---- Local imports

from qwatson.watson.watson import Watson
from qwatson.utils import icons
from qwatson.utils.dates import round_watson_frame
from qwatson.widgets.clock import ElapsedTimeLCDNumber
from qwatson.widgets.dates import DateRangeNavigator
from qwatson.widgets.tableviews import WatsonDailyTableWidget
from qwatson.widgets.toolbar import (
    OnOffToolButton, QToolButtonSmall, DropDownToolButton)
from qwatson import __namever__
from qwatson.models.tablemodels import WatsonTableModel
from qwatson.views.activitydialog import ActivityInputDialog
from qwatson.widgets.layout import ColoredFrame


class QWatson(QWidget):

    def __init__(self, debug=False, parent=None):
        super(QWatson, self).__init__(parent)
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowTitle(__namever__)
        self.setMinimumWidth(300)
        self.setWindowFlags(Qt.Window |
                            Qt.WindowMinimizeButtonHint |
                            Qt.WindowCloseButtonHint)

        if debug is True:
            config_dir = osp.join(osp.dirname(__file__), 'tests', 'watson')
        else:
            config_dir = None

        if platform.system() == 'Windows':
            import ctypes
            myappid = __namever__
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                myappid)

        self.client = Watson(config_dir=config_dir)
        self.model = WatsonTableModel(self.client)
        if self.client.is_started:
            self.stop_watson(message="last session not closed correctly.",
                             tags=['error'])

        self.overview_widg = WatsonOverviewWidget(self.client, self.model)
        self.setup()

    def setup(self):
        """Setup the widget with the provided arguments."""
        timebar = self.setup_timebar()
        self.activity_input_dial = self.setup_activity_input_dial()
        statusbar = self.setup_statusbar()

        # ---- Setup layout

        mainlayout = QGridLayout(self)
        mainlayout.setContentsMargins(0, 0, 0, 0)
        mainlayout.setSpacing(0)
        mainlayout.addWidget(self.activity_input_dial, 1, 0)
        mainlayout.addWidget(timebar, 0, 0)
        mainlayout.addWidget(statusbar, 2, 0)

    def setup_activity_input_dial(self):
        """
        Setup the embedded dialog to setup the current activity parameters.
        """
        activity_input_dial = ActivityInputDialog()
        activity_input_dial.set_background_color('light')
        activity_input_dial.set_projects(self.client.projects)

        activity_input_dial.sig_project_removed.connect(self.project_removed)
        activity_input_dial.sig_project_renamed.connect(self.project_renamed)
        activity_input_dial.sig_project_added.connect(self.new_project_added)
        activity_input_dial.sig_project_changed.connect(self.project_changed)

        # Set current activity inputs to the last ones savec in the database.
        if len(self.client.frames) > 0:
            activity_input_dial.set_current_project(self.client.frames[-1][2])
            activity_input_dial.set_tags(self.client.frames[-1].tags)
            activity_input_dial.set_comment(self.client.frames[-1].message)

        return activity_input_dial

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

    # ---- Bottom toolbar

    def setup_statusbar(self):
        """Setup the toolbar located at the bottom of the main widget."""
        self.btn_report = QToolButtonSmall('note')
        self.btn_report.clicked.connect(self.overview_widg.show)
        self.btn_report.setToolTip(
            "<b>Activity Overview</b><br><br>"
            "Open the activity overview window.")

        self.round_minutes = {
            'round to 1min': 1, 'round to 5min': 5, 'round to 10min': 10}
        self.round_time_btn = DropDownToolButton(style='text_only')
        self.round_time_btn.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
        self.round_time_btn.addItems(list(self.round_minutes.keys()))
        self.round_time_btn.setCurrentIndex(1)
        self.round_time_btn.setToolTip(
            "<b>Round Start and Stop</b><br><br>"
            "Round start and stop times to the nearest"
            " multiple of the selected factor.")

        # Setup the layout of the statusbar

        statusbar = ColoredFrame()
        statusbar.set_background_color('window')

        layout = QGridLayout(statusbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.round_time_btn, 0, 0)
        layout.addWidget(self.btn_report, 0, 2)
        layout.setColumnStretch(1, 100)

        return statusbar

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

    def new_project_added(self, name):
        """Handle when a new project is added in the manager."""
        pass

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
            self.client.start(self.activity_input_dial.project)
            self.elap_timer.start()
        else:
            self.elap_timer.stop()
            self.stop_watson(message=self.activity_input_dial.comment,
                             project=self.activity_input_dial.project,
                             tags=self.activity_input_dial.tags)

    def stop_watson(self, message=None, project=None, tags=None):
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
        self.client.frames[-1] = round_watson_frame(
            self.client.frames[-1],
            self.round_minutes[self.round_time_btn.text()])

        self.client.save()
        self.model.endInsertRows()

    def closeEvent(self, event):
        """Qt method override."""
        self.client.save()
        event.accept()


class WatsonOverviewWidget(QWidget):
    """A widget to show and edit activities logged with Watson."""
    def __init__(self, client, model, parent=None):
        super(WatsonOverviewWidget, self).__init__(parent)
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowTitle("Activity Overview")

        self.setup(model)
        self.date_span_changed()

    def setup(self, model):
        """Setup the widget with the provided arguments."""
        self.table_widg = WatsonDailyTableWidget(model, parent=self)

        self.date_range_nav = DateRangeNavigator()
        self.date_range_nav.sig_date_span_changed.connect(
            self.date_span_changed)

        # ---- Setup the layout

        layout = QGridLayout(self)
        layout.addWidget(self.date_range_nav)
        layout.addWidget(self.table_widg)

    def date_span_changed(self):
        """Handle when the range of the date range navigator widget change."""
        self.table_widg.set_date_span(self.date_range_nav.current)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    watson_gui = QWatson()
    watson_gui.show()
    watson_gui.setFixedSize(watson_gui.size())
    app.exec_()
