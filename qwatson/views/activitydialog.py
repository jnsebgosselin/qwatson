# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys

# ---- Third party imports

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import (QApplication, QGridLayout, QLabel,
                             QLineEdit, QMessageBox, QWidget)

# ---- Local imports

from qwatson.widgets.comboboxes import ComboBoxEdit
from qwatson.widgets.toolbar import ToolBarWidget, QToolButtonSmall
from qwatson.widgets.layout import ColoredFrame
from qwatson.widgets.tags import TagLineEdit
from qwatson.utils import icons


class ActivityInputDialog(ColoredFrame):
    """A dialog to setup the parameters of the currently running activity."""

    sig_project_added = QSignal(str)
    sig_project_changed = QSignal(int)
    sig_project_removed = QSignal(str)
    sig_project_renamed = QSignal(str, str)

    def __init__(self, parent=None):
        super(ActivityInputDialog, self).__init__(parent)

        self.project_manager = self.setup_project_manager()

        self.tag_lineedit = TagLineEdit()
        self.tag_lineedit.setPlaceholderText("Tags (comma separated)")

        self.msg_textedit = QLineEdit()
        self.msg_textedit.setPlaceholderText("Comment")

        # ---- Setup the layout

        layout = QGridLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        layout.addWidget(self.project_manager, 0, 1)
        layout.addWidget(self.tag_lineedit, 1, 1)
        layout.addWidget(self.msg_textedit, 2, 1)

        layout.addWidget(QLabel('project :'), 0, 0)
        layout.addWidget(QLabel('tags :'), 1, 0)
        layout.addWidget(QLabel('comment :'), 2, 0)

    def setup_project_manager(self):
        """Setup the widget to manage projects."""
        project_manager = ProjectManager()

        # Relay signals.
        project_manager.sig_project_added.connect(self.sig_project_added.emit)
        project_manager.sig_project_changed.connect(
            self.sig_project_changed.emit)
        project_manager.sig_project_removed.connect(
            self.sig_project_removed.emit)
        project_manager.sig_project_renamed.connect(
            self.sig_project_renamed.emit)

        return project_manager

    @property
    def comment(self):
        """Return the text of the comment line edit."""
        return self.msg_textedit.text()

    @property
    def tags(self):
        """Return the tags listed in the tag line edit."""
        return self.tag_lineedit.tags

    @property
    def project(self):
        """Return the currently selected project in the project manager."""
        return self.project_manager.current_project

    def set_current_project(self, project):
        """Set the current project of the project manager."""
        self.project_manager.set_current_project(project)

    def set_tags(self, tags):
        """Set the tag list shown in the tag line edit."""
        self.tag_lineedit.set_tags(tags)

    def set_comment(self, comment):
        """Set the comment shown in the comment line edit."""
        self.msg_textedit.setText(comment)

    def set_projects(self, project):
        """Set the list of project in the project manager."""
        self.project_manager.set_project_list(project)


class ProjectManager(QWidget):
    """
    A toolbar composed of a combobox to show the existing projects and
    toolbuttons to edit, add, and delete project from the combobox.
    """
    sig_project_renamed = QSignal(str, str)
    sig_project_added = QSignal(str)
    sig_project_changed = QSignal(int)
    sig_project_removed = QSignal(str)

    def __init__(self, projects=[], parent=None):
        super(ProjectManager, self).__init__(parent)

        self.setup()
        self.set_project_list(projects)

    def setup(self):
        """Setup the widget with the provided arguments."""

        self.project_cbox = self.setup_combobox()
        self.toolbar = self.setup_toolbar()

        layout = QGridLayout(self)

        layout.addWidget(self.project_cbox, 0, 0)
        layout.addWidget(self.toolbar, 0, 1)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setColumnStretch(0, 100)

    def setup_combobox(self):
        """
        Setup the combobox where project can be selected, added, edited, and
        removed.
        """
        project_cbox = ComboBoxEdit()

        # Relay signals from the combobox.
        project_cbox.setFixedHeight(icons.get_iconsize('small').height())
        project_cbox.sig_item_renamed.connect(self.sig_project_renamed.emit)
        project_cbox.sig_item_added.connect(self.sig_project_added.emit)
        project_cbox.currentIndexChanged.connect(self.project_changed)

        return project_cbox

    def setup_toolbar(self):
        """Setup the main toolbar of the widget"""
        toolbar = ToolBarWidget()

        self.btn_add = QToolButtonSmall('plus')
        self.btn_add.clicked.connect(self.btn_add_isclicked)
        self.btn_add.setToolTip("Add a new project")

        self.btn_rename = QToolButtonSmall('edit')
        self.btn_rename.clicked.connect(self.btn_rename_isclicked)
        self.btn_rename.setToolTip("Rename the current project")

        self.btn_remove = QToolButtonSmall('clear')
        self.btn_remove.clicked.connect(self.btn_remove_isclicked)
        self.btn_remove.setToolTip("Delete the current project")

        items = [self.btn_add, self.btn_rename, self.btn_remove]
        for item in items:
            toolbar.addWidget(item)

        return toolbar

    # ---- Buttons handlers

    def project_changed(self, index):
        """Handle when the project selection change in the combobox."""
        self.btn_rename.setEnabled(index != -1)
        self.btn_remove.setEnabled(index != -1)
        self.sig_project_changed.emit(index)

    def btn_add_isclicked(self):
        """Handle when the button to add a new project is clicked."""
        self.project_cbox.set_edit_mode('add')

    def btn_rename_isclicked(self):
        """Handle when the button to rename a new project is clicked."""
        self.project_cbox.set_edit_mode('rename')

    def btn_remove_isclicked(self):
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
            self.sig_project_removed.emit(project)

    # ---- Project combobox handlers

    @property
    def current_project(self):
        """Return the currently selected project."""
        return self.project_cbox.currentText()

    def set_project_list(self, projects):
        """Add a the project list to the project combobox."""
        self.project_cbox.clear()
        self.project_cbox.addItems(projects)

    def set_current_project(self, project):
        """Set the current project to project in the combobox."""
        self.project_cbox.setCurentText(project)
        self.sig_project_changed.emit(self.project_cbox.currentIndex())
        self.project_changed(self.project_cbox.currentIndex())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    activity_input_dialog = ActivityInputDialog()
    activity_input_dialog.show()
    app.exec_()
