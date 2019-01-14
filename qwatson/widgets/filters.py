# -*- coding: utf-8 -*-

# Copyright © Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys

# ---- Third party imports

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu, QWidgetAction, QCheckBox

# ---- Local imports

from qwatson.widgets.toolbar import QToolButtonBase


class FilterButton(QToolButtonBase):
    """
    A tool button to that contains a menu with a list of all projects and tags
    that can be checked in order to filter which activities are shown in the
    overview table.
    """

    def __init__(self, client=None):
        super().__init__('filters', 'small', None)
        self.setPopupMode(self.InstantPopup)
        self.client = client
        self.setup_menu()

    def setup_menu(self):
        """Setup the button menu.""" 
        menu = QMenu()

        self.projects_menu = FilterProjectsMenu(self.client, self)
        menu.addMenu(self.projects_menu)

        self.tags_menu = FilterTagsMenu(self.client, self)
        menu.addMenu(self.tags_menu)

        self.setMenu(menu)


class FilterBaseMenu(QMenu):
    """
    A base class menu that contains a list of checkable items and a
    (Select All) item that allow checking or un-checking all the menu items
    at once.
    """
    checked_items_changed = QSignal(list)

    def __init__(self, name, client=None, parent=None):
        super().__init__(name, parent)
        self._actions = {}
        self.client = client
        self.aboutToShow.connect(self.setup_menu_items)
        self.setup_menu_items()

    def items(self):
        """
        Return a list of strings corresponding to the name of all the items
        that should appear in the menu.
        """
        raise NotImplementedError
        
    def checked_items(self):
        """
        Return a list of strings with the name of the items that are
        checked in the menu.
        """
        return [item for item in self.items() if
                self._actions[item].defaultWidget().isChecked()]

    def setup_menu_items(self):
        """
        Setup the items listed in the menu, including a (select all) item
        to check or uncheck all items at once.
        """
        self.clear()
        if '__select_all__' not in self._actions:
            checkbox = QCheckBox('(Select All)', self.parent())
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.handle_select_all_items)
            action = QWidgetAction(self.parent())
            action.setDefaultWidget(checkbox)
            self._actions['__select_all__'] = action
        self.addAction(self._actions['__select_all__'])
        if self.client is not None:
            self.addSeparator()
            for item in self.items():
                if item in self._actions:
                    self.addAction(self._actions[item])
                else:
                    checkbox = QCheckBox(item, self.parent())
                    checkbox.setChecked(True)
                    checkbox.stateChanged.connect(self.setup_select_all_items)
                    action = QWidgetAction(self.parent())
                    action.setDefaultWidget(checkbox)
                    self.addAction(action)
                    self._actions[item] = action
            self.setup_select_all_items()

    def setup_select_all_items(self):
        """
        Setup the check state of the (Select All) item depending on the
        check state of the menu items.
        """
        values = [self._actions[item].defaultWidget().isChecked() for
                  item in self.items()]

        checkbox = self._actions['__select_all__'].defaultWidget()
        checkbox.blockSignals(True)
        if all(values):
            checkbox.setTristate(False)
            checkbox.setCheckState(Qt.Checked)
        elif any(values):
            checkbox.setTristate(True)
            checkbox.setCheckState(Qt.PartiallyChecked)
        else:
            checkbox.setTristate(False)
            checkbox.setChecked(False)
        checkbox.blockSignals(False)

    def handle_select_all_items(self):
        """
        Check or un-check all menu items depending on the check state of the
        (Select All) item.
        """
        checkbox = self._actions['__select_all__'].defaultWidget()
        is_all_project_checked = checkbox.isChecked()
        for item in self.items():
            checkbox = self._actions[item].defaultWidget()
            checkbox.blockSignals(True)
            checkbox.setChecked(is_all_project_checked)
            checkbox.blockSignals(False)


class FilterProjectsMenu(FilterBaseMenu):
    """An implementation of the FilterBaseMenu for activity projects."""

    def __init__(self, client=None, parent=None):
        super().__init__('Projects', client, parent)

    def items(self):
        """Base class method implementation."""
        return self.client.projects


class FilterTagsMenu(FilterBaseMenu):
    """An implementation of the FilterBaseMenu for activity tags."""

    def __init__(self, client=None, parent=None):
        super().__init__('Tags', client, parent)

    def items(self):
        """Base class method implementation."""
        return self.client.tags


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout
    from qwatson.watson_ext.watsonextends import Watson

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QGridLayout(window)
    layout.addWidget(FilterButton(Watson()), 0, 0)
    window.show()

    sys.exit(app.exec_())
