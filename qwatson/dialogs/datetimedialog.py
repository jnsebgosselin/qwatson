# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys

# ---- Third party imports

import arrow
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import QDateTime, Qt
from PyQt5.QtWidgets import (QApplication, QDateTimeEdit, QDialogButtonBox,
                             QLabel, QVBoxLayout, QStyleOption, QHBoxLayout)

# ---- Local imports

from qwatson.utils.dates import (local_arrow_from_str,  qdatetime_from_arrow,
                                 local_arrow_from_tuple)
from qwatson.widgets.layout import InfoBox, ColoredFrame


class DateTimeInputDialog(QWidget):
    """
    A dialog to select a datetime value that is built to be enclosed in
    a layout, and not used as a child window.
    """
    sig_accepted = QSignal(arrow.Arrow)
    sig_rejected = QSignal(arrow.Arrow)
    sig_closed = QSignal()

    DEFAULT_MIN_DATETIME = local_arrow_from_tuple((2000, 1, 1))

    def __init__(self, parent=None):
        super(DateTimeInputDialog, self).__init__(parent)
        self._minimum_datetime = None
        self.setup()

    def setup(self):
        """Setup the dialog widgets and layout."""
        self.datetime_edit = self.setup_datetime_edit()
        self.button_box = self.setup_dialog_button_box()
        info_text = ("The start time cannot be sooner than the stop\n"
                     " time of the last saved activity and later than\n"
                     " the current time")
        info_box = InfoBox(info_text, 'info', 'small')

        # Setup the layout of the dialog

        layout = QGridLayout(self)
        layout.addWidget(
            QLabel('Enter the start time for the activity :'), 0, 0)
        layout.addWidget(self.datetime_edit, 1, 0)
        layout.addWidget(info_box, 3, 0)
        layout.addWidget(self.button_box, 5, 0)

        layout.setRowStretch(2, 100)
        layout.setRowStretch(4, 100)

    def setup_datetime_edit(self):
        """Setup the datetune edit widget."""
        datetime_edit = QDateTimeEdit()
        datetime_edit.setCalendarPopup(True)
        datetime_edit.setDisplayFormat("yyyy-MM-dd  hh:mm")
        datetime_edit.setKeyboardTracking(False)
        datetime_edit.dateTimeChanged.connect(self.validate_datetime)

        ft = datetime_edit.font()
        ft.setPointSize(ft.pointSize() + 2)
        datetime_edit.setFont(ft)

        return datetime_edit

    def setup_dialog_button_box(self):
        """Setup the buttons of the dialog."""
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(
            lambda: self.sig_accepted.emit(self.get_datetime_arrow()))
        button_box.rejected.connect(
            lambda: self.sig_rejected.emit(self.get_datetime_arrow()))
        button_box.accepted.connect(lambda: self.sig_closed.emit())
        button_box.rejected.connect(lambda: self.sig_closed.emit())

        return button_box

    @property
    def minimum_datetime(self):
        """Return the minimum datetime that is accepted by the dialog."""
        if self._minimum_datetime is None:
            return self.DEFAULT_MIN_DATETIME
        else:
            return self._minimum_datetime

    def set_datetime_minimum(self, value):
        """Set the minimum datetime allowed by the dialog."""
        self._minimum_datetime = value

    @QSlot(QDateTime)
    def validate_datetime(self, qdatetime):
        """
        Set the datetime value of the datetime edit widet to the specified
        minimum or maximum value if the current value is not enclosed in
        these two limits.
        """
        current_datetime = self.get_datetime_arrow()
        if current_datetime < self.minimum_datetime:
            self.datetime_edit.setDateTime(
                qdatetime_from_arrow(self.minimum_datetime))
        elif current_datetime > arrow.now():
            self.datetime_edit.setDateTime(
                qdatetime_from_arrow(arrow.now()))

    def set_datetime_to_now(self):
        """Set the current datetime of the datetime edit to now."""
        self.datetime_edit.setDateTime(qdatetime_from_arrow(arrow.now()))

    def get_datetime_arrow(self):
        """Return the current datetime in arrow format."""
        return local_arrow_from_str(
                   self.datetime_edit.dateTime().toString("yyyy-MM-dd hh:mm"),
                   fmt='YYYY-MM-DD HH:mm')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    date_time_dialog = DateTimeInputDialog()
    date_time_dialog.setFixedSize(300, 162)
    date_time_dialog.set_datetime_to_now()
    date_time_dialog.show()
    app.exec_()
