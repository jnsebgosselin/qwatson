# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Imports: Third Parties

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtWidgets import (QApplication, QGridLayout, QLineEdit, QComboBox,
                             QWidget)


class ComboBoxEdit(QWidget):
    currentIndexChanged = QSignal(int)
    sig_item_renamed = QSignal(str, str)
    sig_item_added = QSignal(str)

    def __init__(self, parent=None):
        super(ComboBoxEdit, self).__init__(parent)
        self._edit_mode = None
        self.setup()

    def setup(self):
        """Setup the combobox edit."""

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
        """Extend Qt method setFixedHeight."""
        self.linedit.setFixedHeight(height)
        self.combobox.setFixedHeight(height)
        super(ComboBoxEdit, self).setFixedHeight(height)

    def eventFilter(self, widget, event):
        """
        Check for events to accept the edits and modify the content of the
        combobox accordingly.
        """
        is_focusout = event.type() == QEvent.FocusOut
        is_keypress = event.type() == QEvent.KeyPress

        is_canceled = (
            is_keypress and event.key() == Qt.Key_Escape
            ) and self._edit_mode is not None
        is_accepted = (
            is_focusout or
            (is_keypress and event.key() in [Qt.Key_Enter, Qt.Key_Return])
            ) and self._edit_mode is not None
        is_finished = is_accepted or is_canceled

        new_name = self.linedit.text()
        if is_accepted and new_name:
            new_name_exists = self.combobox.findText(new_name) != -1
            if self._edit_mode == 'add':
                if new_name_exists is False:
                    self.combobox.addItem(new_name)
                    self.setCurentText(new_name)
                    self.sig_item_added.emit(new_name)
                else:
                    self.setCurentText(new_name)
            elif self._edit_mode == 'rename':
                old_name = self.combobox.currentText()
                if old_name != new_name:
                    current_index = self.combobox.currentIndex()
                    self.combobox.removeItem(current_index)
                    if new_name_exists is False:
                        self.combobox.insertItem(current_index, new_name)
                    self.setCurentText(new_name)
                    self.sig_item_renamed.emit(old_name, new_name)

        if is_finished:
            self._edit_mode = None
            self.linedit.clear()
            self.combobox.setVisible(True)
            self.combobox.setFocus()
            self.linedit.setVisible(False)

        return QWidget.eventFilter(self, widget, event)

    def currentText(self):
        """Return the current text of the combobox."""
        return self.combobox.currentText()

    def currentIndex(self):
        """Return the current index of the combobox."""
        return self.combobox.currentIndex()

    def setCurentText(self, name):
        """Set the combobox to the index matching the provided name."""
        self.combobox.blockSignals(True)
        self.combobox.setCurrentIndex(self.combobox.findText(name))
        self.combobox.blockSignals(False)

    def clear(self):
        """Clear all the items from the combobox."""
        self.combobox.clear()

    def addItems(self, items):
        """Add the items to the combobox."""
        self.combobox.addItems(items)

    def count(self):
        """Return the number of items listed in the combobox."""
        return self.combobox.count()

    def items(self):
        """Return a list of all the items listed in the combobox."""
        return [self.combobox.itemText(i) for i in range(self.count())]

    def removeItem(self, index):
        """Remove the item at the specified index in the combobox."""
        self.combobox.removeItem(index)

    def set_edit_mode(self, mode):
        """
        Enter edit mode either to add a new item or to rename an existing
        item.
        """
        if mode in ['add', 'rename']:
            self._edit_mode = mode
            if mode == 'rename':
                self.linedit.setText(self.combobox.currentText())
            elif mode == 'add':
                self.linedit.clear()
        else:
            self._edit_mode = None
        self.linedit.setVisible(self._edit_mode is not None)
        self.linedit.setFocus(self._edit_mode is not None)
        self.combobox.setVisible(self._edit_mode is None)
        self.combobox.setFocus(self._edit_mode is None)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    comboboxedit = ComboBoxEdit()
    comboboxedit.addItems(['item1', 'item2', 'item3'])
    comboboxedit.setCurentText('item1')
    comboboxedit.show()
    app.exec_()
