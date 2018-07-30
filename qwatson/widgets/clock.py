# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import time
import sys

# ---- Third party imports

import arrow
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QLCDNumber, QApplication, QGridLayout, QProxyStyle, QStyle

# ---- Local imports

from qwatson.utils import icons
from qwatson.widgets.layout import ColoredFrame
from qwatson.widgets.toolbar import (
    OnOffToolButton, QToolButtonSmall, QToolButtonBase, DropDownToolButton)

# https://stackoverflow.com/questions/14478574/
# changing-the-digit-color-of-qlcd-number


class StopWatchWidget(ColoredFrame):
    sig_btn_start_clicked = QSignal()
    sig_btn_stop_clicked = QSignal()
    sig_btn_cancel_clicked = QSignal()

    def __init__(self, parent=None):
        super().__init__('window', parent)
        self._startfrom = None
        self.setup()

    def setup(self):
        """Setup the widget layout and child widgets."""
        btn_start = QToolButtonBase('process_start', 'normal')
        btn_start.setToolTip(
            "<b>Start</b><br><br>"
            "Start monitoring the elapsed time for an activity.<br><br>"
            " The \"Start from\" menu located in the statusbar below can be"
            " used to specify a different start time for the activity."
            " The project, tags, and comment for the activity can be specified"
            " in the section below.<br><br>"
            " Note that the start time, project, tags, and comment are saved"
            " to the database only when the button \"Stop\" is clicked."
            " It is thus possible to modify the value of these parameters"
            " while the activity is being monitored."
            )
        btn_start.clicked.connect(lambda: self.sig_btn_start_clicked.emit())

        btn_stop = QToolButtonBase(icon='process_stop', iconsize='normal')
        btn_stop.setToolTip(
            "<b>Stop</b>")
        btn_stop.clicked.connect(lambda: self.sig_btn_stop_clicked.emit())
        btn_stop.setEnabled(False)

        btn_cancel = QToolButtonBase(icon='process_cancel', iconsize='normal')
        btn_cancel.setToolTip(
            "<b>Cancel</b>")
        btn_cancel.clicked.connect(lambda: self.sig_btn_cancel_clicked.emit())
        btn_cancel.setEnabled(False)

        self.buttons = {'start': btn_start,
                        'stop': btn_stop,
                        'cancel': btn_cancel}

        btn_toolbar = QGridLayout()
        btn_toolbar.setSpacing(1)
        btn_toolbar.setContentsMargins(0, 0, 0, 0)
        btn_toolbar.addWidget(btn_start, 1, 0)
        btn_toolbar.addWidget(btn_stop, 1, 1)
        btn_toolbar.addWidget(btn_cancel, 1, 2)
        btn_toolbar.setRowStretch(0, 100)
        btn_toolbar.setRowStretch(2, 100)

        self.elap_timer = ElapsedTimeLCDNumber()
        size_hint = self.elap_timer.sizeHint()
        size_ratio = size_hint.width()/size_hint.height()
        self.elap_timer.setFixedHeight(icons.get_iconsize('large').height())
        self.elap_timer.setMinimumWidth(self.elap_timer.height() * size_ratio)

        layout = QGridLayout(self)
        layout.addLayout(btn_toolbar, 0, 0)
        layout.setRowStretch(1, 100)
        layout.addWidget(self.elap_timer, 0, 2)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 5, 5, 5)

    def start(self, startfrom=None):
        self.setStartFrom(startfrom)
        self.buttons['start'].setEnabled(False)
        self.buttons['stop'].setEnabled(True)
        self.buttons['cancel'].setEnabled(True)
        self.elap_timer.start(self.startFrom().timestamp)

    def stop(self):
        self.buttons['start'].setEnabled(True)
        self.buttons['stop'].setEnabled(False)
        self.buttons['cancel'].setEnabled(False)
        self.elap_timer.stop()

    def cancel(self):
        self.buttons['start'].setEnabled(True)
        self.buttons['stop'].setEnabled(False)
        self.buttons['cancel'].setEnabled(False)
        self.elap_timer.cancel()

    def isRunning(self):
        """Return wheter the stopwatch is currently running."""
        return self.elap_timer.is_started

    def startFrom(self):
        """
        Return the reference arrow used to calcul the elapsed time when the
        stopwatch is running.
        """
        return arrow.now() if self._startfrom is None else self._startfrom

    def setStartFrom(self, x):
        """
        Set the reference arrow used to calcul the elapsed time when the stop
        watch is running.
        """
        self._startfrom


class ElapsedTimeLCDNumber(QLCDNumber):
    """A widget that displays elapsed time in digital format."""

    def __init__(self, parent=None):
        super(ElapsedTimeLCDNumber, self).__init__(parent)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_elapsed_time)

        self.setDigitCount(8)
        self.setSegmentStyle(QLCDNumber.Flat)
        self.display(time.strftime("%H:%M:%S", time.gmtime(0)))
        self.setFrameStyle(0)

        self.is_started = False
        self._start_time = time.time()
        self.update_elapsed_time()

    def start(self, start_time=None):
        """Start the elapsed time counter."""
        self._start_time = time.time() if start_time is None else start_time
        self.update_elapsed_time()
        self.timer.start(10)
        self.is_started = True

    def stop(self):
        """Stop the elapsed time counter."""
        self.timer.stop()
        self.is_started = False

    def cancel(self):
        """Stop and reset the elapsed time counter."""
        self.timer.stop()
        self.is_started = False
        self.reset_elapsed_time()

    def update_elapsed_time(self):
        """Update elapsed time in the widget."""
        self._elapsed_time = time.time() - self._start_time
        self.display(
            time.strftime("%H:%M:%S", time.gmtime(self._elapsed_time)))

    def reset_elapsed_time(self):
        """Reset the elpased time to 00:00:00 in the widget."""
        self._elapsed_time = 0
        self.display(time.strftime("%H:%M:%S", time.gmtime(0)))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    activity_stop_watch = StopWatchWidget()
    activity_stop_watch.show()
    app.exec_()
