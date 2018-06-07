# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys
import platform


# ---- Third parties imports

from PyQt5.QtCore import (Qt, QModelIndex)
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QLabel,
                             QMessageBox, QSizePolicy, QTextEdit)

# ---- Local imports

from qwatson.watson.watson import Watson
from qwatson.utils import icons
from qwatson.widgets.comboboxes import ComboBoxEdit
from qwatson.widgets.clock import ElapsedTimeLCDNumber
from qwatson.widgets.dates import DateRangeNavigator
from qwatson.widgets.tableviews import WatsonDailyTableWidget
from qwatson.widgets.toolbar import (ToolBarWidget, OnOffToolButton,
                                     QToolButtonSmall)
from qwatson import __namever__
from qwatson.models.tablemodels import WatsonTableModel


class QWatson(QWidget):

    def __init__(self, parent=None):
        super(QWatson, self).__init__(parent)
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowTitle(__namever__)
        self.setWindowFlags(Qt.Window |
                            Qt.WindowMinimizeButtonHint |
                            Qt.WindowCloseButtonHint)

        if platform.system() == 'Windows':
            import ctypes
            myappid = __namever__
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                myappid)

        self.client = Watson()
        self.model = WatsonTableModel(self.client)
        if self.client.is_started:
            self.stop_watson(message="last session not closed correctly.")

        self.overview_widg = WatsonOverviewWidget(self.client, self.model)
        self.setup()

    def setup(self):
        """Setup the widget with the provided arguments."""
        timebar = self.setup_timebar()
        self.setup_toolbar()
        self.setup_project_cbox()

        self.msg_textedit = QTextEdit()
        self.msg_textedit.setPlaceholderText("Description")
        self.msg_textedit.setMaximumHeight(50)
        self.msg_textedit.setSizePolicy(
                QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))

        layout = QGridLayout(self)
        layout.addWidget(QLabel('Project :'), 0, 0)
        layout.addWidget(self.project_cbox, 0, 1)
        layout.addWidget(self.toolbar, 0, 2)
        layout.addWidget(self.msg_textedit, 1, 0, 1, 3)
        layout.addWidget(timebar, 2, 0, 1, 3)

        layout.setColumnStretch(1, 100)
        layout.setRowStretch(1, 100)

    def setup_project_cbox(self, name=None):
        """
        Setup the list of all the existing projects, sorted by name, in a
        combobox.
        """
        self.project_cbox = ComboBoxEdit()
        self.project_cbox.setFixedHeight(icons.get_iconsize('small').height())

        self.project_cbox.currentIndexChanged.connect(self.project_changed)
        self.project_cbox.sig_item_renamed.connect(self.project_renamed)
        self.project_cbox.sig_item_added.connect(self.new_project_added)

        self.project_cbox.addItems(self.client.projects)
        if len(self.client.frames) > 0:
            self.project_cbox.setCurentText(self.client.frames[-1][2])
        self.project_changed(self.project_cbox.currentIndex())

    def setup_toolbar(self):
        """Setup the main toolbar of the widget"""
        self.toolbar = ToolBarWidget()

        self.btn_add = QToolButtonSmall('plus')
        self.btn_add.clicked.connect(self.btn_add_isclicked)
        self.btn_add.setToolTip("Create a new project")

        self.btn_rename = QToolButtonSmall('edit')
        self.btn_rename.clicked.connect(self.btn_rename_isclicked)
        self.btn_rename.setToolTip("Rename the current project")

        self.btn_del = QToolButtonSmall('clear')
        self.btn_del.clicked.connect(self.btn_del_isclicked)
        self.btn_del.setToolTip("Delete the current project")

        self.btn_report = QToolButtonSmall('note')
        self.btn_report.clicked.connect(self.overview_widg.show)
        self.btn_report.setToolTip("Open the overview window")

        # ---- Populate the toolbar

        items = [self.btn_add, self.btn_rename,
                 self.btn_del, None, self.btn_report]
        for item in items:
            self.toolbar.addWidget(item)

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

        timebar = QWidget()
        layout = QGridLayout(timebar)
        layout.addWidget(self.btn_startstop, 0, 0)
        layout.addWidget(self.elap_timer, 0, 1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setColumnStretch(2, 100)

        return timebar

    # ---- Project combobox handlers

    def project_changed(self, index):
        """Handle when the project selection change in the combobox."""
        self.btn_startstop.setEnabled(index != -1)
        self.btn_rename.setEnabled(index != -1)
        self.btn_del.setEnabled(index != -1)

    def project_renamed(self, old_name, new_name):
        """Handle when a project is renamed in the combobox."""
        if old_name != new_name:
            self.model.beginResetModel()
            self.client.rename_project(old_name, new_name)
            self.model.endResetModel()

    def new_project_added(self, name):
        """Handle when a new project is added in the combobox."""
        pass

    # ---- Toolbar handlers

    def btn_startstop_isclicked(self):
        """Handle when the button to start and stop Watson is clicked."""
        if self.btn_startstop.value():
            self.client.start(self.project_cbox.currentText())
            self.elap_timer.start()
        else:
            self.elap_timer.stop()
            self.stop_watson(message=self.msg_textedit.toPlainText(),
                             project=self.project_cbox.currentText())

        self.project_cbox.setEnabled(not self.btn_startstop.value())
        self.btn_add.setEnabled(not self.btn_startstop.value())
        self.btn_rename.setEnabled(not self.btn_startstop.value())
        self.btn_del.setEnabled(not self.btn_startstop.value())

    def stop_watson(self, message=None, project=None):
        """Stop Watson and update the table model."""
        if message is not None:
            self.client._current['message'] = message
        if project is not None:
            self.client._current['project'] = project

        self.model.beginInsertRows(
            QModelIndex(), len(self.client.frames), len(self.client.frames))
        self.client.stop()
        self.client.save()
        self.model.endInsertRows()

    def btn_add_isclicked(self):
        """Handle when the button to add a new project is clicked."""
        self.project_cbox.set_edit_mode('add')

    def btn_rename_isclicked(self):
        """Handle when the button to rename a new project is clicked."""
        self.project_cbox.set_edit_mode('rename')

    def btn_del_isclicked(self):
        """Handle when the button to delete a project is clicked."""
        project = self.project_cbox.currentText()
        index = self.project_cbox.currentIndex()

        msg = ("Are you sure that you want to delete project %s and all "
               " related frames?<br><br>All data will be lost."
               ) % project
        ans = QMessageBox.question(self, 'Delete project', msg,
                                   defaultButton=QMessageBox.No)

        if ans == QMessageBox.Yes:
            self.project_cbox.removeItem(index)
            if project in self.client.projects:
                self.model.beginResetModel()
                self.client.delete_project(project)
                self.model.endResetModel()

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
