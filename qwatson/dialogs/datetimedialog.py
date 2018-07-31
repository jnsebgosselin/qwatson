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
from PyQt5.QtWidgets import (QApplication, QDateTimeEdit, QLabel, QVBoxLayout,
                             QHBoxLayout, QPushButton)

# ---- Local imports

from qwatson.dialogs.basedialog import BaseDialog
from qwatson.utils.dates import (local_arrow_from_str,  qdatetime_from_arrow,
                                 local_arrow_from_tuple)
from qwatson.widgets.layout import InfoBox, ColoredFrame


class DateTimeInputDialog(BaseDialog):
    """
    A dialog to select a datetime value that is built to be enclosed in
    a layout, and not used as a child window.
    """
    DEFAULT_MIN_DATETIME = local_arrow_from_tuple((2000, 1, 1))

    def __init__(self, parent=None):
        super(DateTimeInputDialog, self).__init__(parent)
        self._minimum_datetime = None

    # ---- Setup layout

    def setup(self):
        """Setup the dialog widgets and layout."""
        datetime_box = self.setup_datetime_box()

        # Add buttons to the dialog

        self.add_dialog_button(QPushButton('Start'), 'Start', True)
        self.add_dialog_button(QPushButton('Cancel'), 'Cancel')

        # Setup the info box

        info_text = ("The start time cannot be sooner than the stop time of"
                     " the last saved activity and later than the current"
                     " time.")

        info_box = InfoBox(info_text, 'information', 'small')
        info_box.setContentsMargins(5, 10, 5, 10)
        info_box.setSpacing(10)

        # Setup the layout of the dialog

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(datetime_box)
        layout.addWidget(self.button_box)
        layout.addWidget(info_box)
        layout.setStretch(2, 100)

    def setup_datetime_box(self):
        """Setup the datetime edit widget and a label."""
        self.datetime_edit = datetime_edit = QDateTimeEdit()
        datetime_edit.setCalendarPopup(True)
        datetime_edit.setDisplayFormat("yyyy-MM-dd  hh:mm")
        datetime_edit.setKeyboardTracking(False)
        datetime_edit.dateTimeChanged.connect(self.validate_datetime)
        datetime_edit.setAlignment(Qt.AlignLeft)

        ft = datetime_edit.font()
        ft.setPointSize(ft.pointSize() + 4)
        datetime_edit.setFont(ft)

        label = QLabel('Start time :')
        label.setFont(ft)

        # Setup the layout

        datetime_box = ColoredFrame()
        datetime_box.set_background_color('window')
        layout = QHBoxLayout(datetime_box)
        layout.setContentsMargins(5, 10, 5, 10)
        layout.setSpacing(15)
        layout.addWidget(label)
        layout.addWidget(datetime_edit)
        layout.setStretch(1, 100)

        return datetime_box

    # ---- Bind dialog with main

    def show(self):
        """Qt method override."""
        self.set_datetime_to_now()
        if self.main is not None:
            frames = self.main.client.frames
            self.set_datetime_minimum(
                None if len(frames) == 0 else frames[-1].stop)
        super(DateTimeInputDialog, self).show()

    def receive_answer(self, answer):
        """
        Handle when the value displayed in the datetime widget is accepted
        or canceled by the user.
        """
        if self.main is not None:
            if answer == 'Start':
                self.main.start_watson(start_time=self.get_datetime_arrow())
            elif answer == 'Cancel':
                self.main.cancel_watson()
            self.main.setCurrentIndex(0)

    # ---- Utility

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
