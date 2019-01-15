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
    sig_projects_checkstate_changed = QSignal(dict)
    sig_tags_checkstate_changed = QSignal(dict)

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
        self.projects_menu.sig_items_checkstate_changed.connect(
            self.sig_projects_checkstate_changed.emit)

        self.tags_menu = FilterTagsMenu(self.client, self)
        menu.addMenu(self.tags_menu)
        self.tags_menu.sig_items_checkstate_changed.connect(
            self.sig_tags_checkstate_changed.emit)

        self.setMenu(menu)


class FilterBaseMenu(QMenu):
    """
    A base class menu that contains a list of checkable items and a
    (Select All) item that allow checking or un-checking all the menu items
    at once.
    """
    sig_items_checkstate_changed = QSignal(dict)

    def __init__(self, name, client=None, parent=None):
        super().__init__(name, parent)
        self._actions = {}
        self.client = client
        self.aboutToShow.connect(self.setup_menu_items)

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

    def items_checkstate(self):
        """
        Return a dict with the checkstate values of all the items that are
        listed in the menu.
        """
        return {item: self._actions[item].defaultWidget().isChecked() for
                item in self.items()}

    def setup_menu_items(self):
        """
        Setup the items listed in the menu, including a (select all) item
        to check or uncheck all items at once.
        """
        self.clear()
        if '__select_all__' not in self._actions:
            checkbox = QCheckBox('(Select All)', self.parent())
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.handle_select_was_clicked)
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
                    checkbox.stateChanged.connect(self.handle_item_was_clicked)
                    action = QWidgetAction(self.parent())
                    action.setDefaultWidget(checkbox)
                    self.addAction(action)
                    self._actions[item] = action
            self.setup_select_all_item()

    def setup_select_all_item(self):
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

    def handle_item_was_clicked(self):
        """
        Handle when one of the item checkboxes listed in the menu is clicked.
        """
        self.setup_select_all_item()
        self.sig_items_checkstate_changed.emit(self.items_checkstate())

    def handle_select_was_clicked(self):
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
        self.sig_items_checkstate_changed.emit(self.items_checkstate())


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
        return [''] + self.client.tags


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout
    from qwatson.watson_ext.watsonextends import Watson

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QGridLayout(window)
    layout.addWidget(FilterButton(Watson()), 0, 0)
    window.show()

    sys.exit(app.exec_())
