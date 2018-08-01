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
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import (QApplication, QGridLayout, QMessageBox, QWidget,
                             QLineEdit, QComboBox)

# ---- Local imports

from qwatson.widgets.toolbar import ToolBarWidget, QToolButtonSmall
from qwatson.utils import icons
from qwatson.models.projectmodel import WatsonProjectModel


class ProjectManager(QWidget):
    """
    A toolbar composed of a combobox to show the existing projects and
    toolbuttons to send request to the QWatson mainwindow to add, rename, or
    delete projects from the databse.
    """
    sig_rename_project = QSignal(str, str)
    sig_add_project = QSignal(str)
    sig_del_project = QSignal(str)
    sig_project_changed = QSignal(int)

    def __init__(self, client, parent=None):
        super(ProjectManager, self).__init__(parent)
        self.client = client
        self.model = WatsonProjectModel(client)
        self.setup()

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
        project_cbox = ProjectView(self.model)
        project_cbox.setFixedHeight(icons.get_iconsize('small').height())

        # Relay signals from the combobox.
        project_cbox.sig_rename_project.connect(self.sig_rename_project.emit)
        project_cbox.sig_add_project.connect(self.sig_add_project.emit)
        project_cbox.currentIndexChanged.connect(self.project_changed)

        return project_cbox

    def setup_toolbar(self):
        """Setup the main toolbar of the widget"""
        toolbar = ToolBarWidget()

        self.btn_add = QToolButtonSmall('plus')
        self.btn_add.clicked.connect(self.project_cbox.add_project)
        self.btn_add.setToolTip(
            "<b>Add Project</b><br><br>"
            "Add a new project to the list of availables projects.")

        self.btn_rename = QToolButtonSmall('edit')
        self.btn_rename.clicked.connect(self.project_cbox.rename_project)
        self.btn_rename.setToolTip(
            "<b>Rename Project</b><br><br>"
            "Rename the currently selected project and update the project of"
            " all related activities.<br><br>"
            "If the new name matches that of an already existing project,"
            " merge the activities of both projects toghether.<br><br>"
            "If no project is selected when renaming, set the project of all"
            " activities that are not currently in a project or merge them"
            " with those of an already existing project if applicable."
            )

        self.btn_remove = QToolButtonSmall('minus')
        self.btn_remove.clicked.connect(self.btn_remove_isclicked)
        self.btn_remove.setToolTip(
            "<b>Delete Project</b><br><br>"
            "Erase permanently the currently selected project and all related"
            " activities.<br><br>"
            "If no project is selected, erase all activities"
            " that are currently not in a project.")

        for item in [self.btn_add, self.btn_remove, self.btn_rename]:
            toolbar.addWidget(item)

        return toolbar

    # ---- Buttons handlers

    def project_changed(self, index):
        """Handle when the project selection change in the combobox."""
        self.btn_rename.setEnabled(index != -1)
        self.btn_remove.setEnabled(index != -1)
        self.sig_project_changed.emit(index)

    def btn_remove_isclicked(self):
        """Handle when the button to delete a project is clicked."""
        self.sig_del_project.emit(self.project_cbox.currentText())

    # ---- Project combobox handlers

    def currentProject(self):
        """Return the currently selected project."""
        return self.project_cbox.currentText()

    def currentProjectIndex(self):
        """Return the index of the currently selected project."""
        return self.project_cbox.currentIndex()

    def setCurrentProject(self, project):
        """Set the current project to project in the combobox."""
        self.project_cbox.setCurentText(project)
        self.project_changed(self.project_cbox.currentIndex())

    def setCurrentProjectIndex(self, index):
        """Set the current index of the combobox to the specified index."""
        self.project_cbox.setCurentIndex(index)
        self.project_changed(self.project_cbox.currentIndex())


class ProjectView(QWidget):
    """
    A QComboxBox underlain with a QLineEdit to display the existing projects
    in the frame database and to add or rename projects to the database.
    """
    currentIndexChanged = QSignal(int)
    sig_rename_project = QSignal(str, str)
    sig_add_project = QSignal(str)

    def __init__(self, model, parent=None):
        super(ProjectView, self).__init__(parent)
        self._edit_mode = None
        self.setup()
        self.combobox.setModel(model)

        # We need to call showPopup on the combobox here to prevent a lag
        # when clicking on the combobox for the first time.
        self.combobox.showPopup()

    def setup(self):
        """Setup the combobox and the lineedit widget."""
        self.linedit = QLineEdit()
        self.linedit.setVisible(False)
        self.linedit.installEventFilter(self)

        self.combobox = QComboBox()
        self.combobox.setEditable(False)
        self.combobox.currentIndexChanged.connect(
            self.currentIndexChanged.emit)

        layout = QGridLayout(self)
        layout.addWidget(self.combobox, 0, 0)
        layout.addWidget(self.linedit, 0, 0)
        layout.setContentsMargins(0, 0, 0, 0)

    def setFixedHeight(self, height):
        """Extend Qt method setFixedHeight."""
        self.linedit.setFixedHeight(height)
        self.combobox.setFixedHeight(height)
        super(ProjectView, self).setFixedHeight(height)

    def currentText(self):
        """Return the current text of the combobox."""
        return self.combobox.currentText()

    def currentIndex(self):
        """Return the current index of the combobox."""
        return self.combobox.currentIndex()

    def setCurentText(self, name):
        """Set the combobox to the index matching the provided name."""
        self.setCurentIndex(self.combobox.findText(name))

    def setCurentIndex(self, index):
        """Set the combobox current index the the specified index."""
        self.combobox.blockSignals(True)
        self.combobox.setCurrentIndex(index)
        self.combobox.blockSignals(False)

    def add_project(self):
        """Show the lineedit to add a project."""
        self._edit_mode = 'add'
        self.linedit.clear()
        self._enter_edit_mode()

    def rename_project(self):
        """Show the lineedit to rename a project."""
        self._edit_mode = 'rename'
        self.linedit.setText(self.combobox.currentText())
        self._enter_edit_mode()

    def _enter_edit_mode(self):
        """
        Enter edit mode either to add a new item or to rename an existing
        item.
        """
        self.linedit.setVisible(True)
        self.linedit.setFocus(True)
        self.combobox.setVisible(False)

    def _leave_edit_mode(self):
        """
        Leave edit mode by hiding the lineedit and showing back the
        combobox.
        """
        self._edit_mode = None
        self.combobox.setVisible(True)
        self.combobox.setFocus()
        self.linedit.setVisible(False)

    def eventFilter(self, widget, event):
        """
        Check for events to accept the edits and modify the content of the
        combobox accordingly.
        """
        if event.type() == QEvent.KeyPress:
            # When pressing the Enter, Return, or Excape key, we set
            # programmatically the focus back to the combobox. This will
            # trigger a FocusOut event on the linedit. This is where we will
            # emit the sig_add_project or sig_rename_project signals.
            if event.key() in [Qt.Key_Enter, Qt.Key_Return]:
                self.combobox.setVisible(True)
                self.combobox.setFocus()
                self.linedit.setVisible(False)
                event.accept()
                return True
            elif event.key() == Qt.Key_Escape:
                self._leave_edit_mode()
                event.accept()
                return True
        elif event.type() == QEvent.FocusOut:
            if self._edit_mode == 'add':
                self.sig_add_project.emit(self.linedit.text())
                self._leave_edit_mode()
            elif self._edit_mode == 'rename':
                self.sig_rename_project.emit(
                    self.combobox.currentText(), self.linedit.text())
                self._leave_edit_mode()

        return QWidget.eventFilter(self, widget, event)


if __name__ == '__main__':
    from qwatson.watson_ext.watsonextends import Watson
    from qwatson import __rootdir__
    import os.path as osp

    dirname = osp.join(__rootdir__, 'widgets', 'tests', 'appdir')
    client = Watson(config_dir=dirname)

    app = QApplication(sys.argv)
    project_manager = ProjectManager(client)
    project_manager.show()
    app.exec_()
