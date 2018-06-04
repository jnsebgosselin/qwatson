# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Imports: Third Parties

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import (QGridLayout, QLineEdit, QComboBox, QWidget)


class ComboBoxEdit(QWidget):
    currentIndexChanged = QSignal(int)
    sig_item_renamed = QSignal(str, str)
    sig_item_added = QSignal(str)

    def __init__(self, parent=None):
        super(ComboBoxEdit, self).__init__(parent)
        self._edit_mode = ''

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
        layout.setColumnStretch(0, 100)
        layout.setContentsMargins(0, 0, 0, 0)

    def setFixedHeight(self, height):
        """Qt method override."""
        self.linedit.setFixedHeight(height)
        self.combobox.setFixedHeight(height)
        super(ComboBoxEdit, self).setFixedHeight(height)

    def eventFilter(self, widget, event):
        accept_event = (
            event.type() == QEvent.FocusOut or
            (event.type() == QEvent.KeyPress and
             event.key() in [Qt.Key_Enter, Qt.Key_Return])
            )

        if accept_event:
            self.linedit.setVisible(False)
            self.combobox.setVisible(True)

            new_name = self.linedit.text()
            self.linedit.clear()
            if new_name:
                if self.combobox.findText(new_name) == -1:
                    if self._edit_mode == 'add':
                        self.combobox.addItem(new_name)
                        self.sig_item_added.emit(new_name)
                    elif self._edit_mode == 'rename':
                        old_name = self.combobox.currentText()
                        current_index = self.combobox.currentIndex()
                        # Update the gui.
                        self.combobox.removeItem(current_index)
                        self.combobox.insertItem(current_index, new_name)
                        # Update the client.
                        self.sig_item_renamed.emit(old_name, new_name)

                self.setCurentText(new_name)
        return QWidget.eventFilter(self, widget, event)

    def currentText(self):
        return self.combobox.currentText()

    def currentIndex(self):
        return self.combobox.currentIndex()

    def setCurentText(self, name):
        self.combobox.blockSignals(True)
        self.combobox.setCurrentIndex(self.combobox.findText(name))
        self.combobox.blockSignals(False)

    def addItems(self, items):
        """Add the items to the combobox."""
        self.combobox.addItems(items)

    def removeItem(self, index):
        self.combobox.removeItem(index)

    def set_edit_mode(self, mode):
        if mode in ['add', 'rename']:
            self._edit_mode = mode
            if mode == 'rename':
                self.linedit.setText(self.combobox.currentText())
            elif mode == 'add':
                self.linedit.clear()
        else:
            self._edit_mode_edit_mode = None
        self.linedit.setVisible(self._edit_mode is not None)
        self.combobox.setVisible(self._edit_mode is None)
