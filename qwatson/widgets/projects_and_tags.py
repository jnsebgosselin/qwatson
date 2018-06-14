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
from PyQt5.QtWidgets import (QApplication, QComboBox, QGridLayout, QLabel,
                             QLineEdit, QMessageBox, QWidget)

# ---- Local imports

from qwatson.widgets.comboboxes import ComboBoxEdit
from qwatson.widgets.toolbar import ToolBarWidget, QToolButtonSmall
from qwatson.utils import icons


class TagManager(QWidget):
    def __init__(self, tags=[], parent=None):
        super(TagManager, self).__init__(parent)
        self.setup()
        self.set_tags(tags)

    def setup(self):
        """Setup the widget with the provided arguments."""
        self.tag_edit = TagLineEdit()
        self.tag_edit.setPlaceholderText("Tags (comma separated)")

        # ---- Setup the layout

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tag_edit)

    @property
    def tags(self):
        """Return the list of tags entered in the tag edit line."""
        return self.tag_edit.tags

    def set_tags(self, tags):
        """Add a the tag list to the tag edit line."""
        self.tag_edit.set_tags(tags)

