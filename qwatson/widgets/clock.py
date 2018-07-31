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
from PyQt5.QtWidgets import (QLCDNumber, QApplication, QGridLayout, QStyle,
                             QStyleOptionToolButton)

# ---- Local imports

from qwatson.utils import icons
from qwatson.widgets.layout import ColoredFrame
from qwatson.widgets.toolbar import QToolButtonBase

# https://stackoverflow.com/questions/14478574/
# changing-the-digit-color-of-qlcd-number


class StopWatchWidget(ColoredFrame):
    """
    A stopwatch widget that consists of a start, stop, and cancel button and
    a digital clock where is shown the elapse time. Clicking on the buttons
    emit signals and do not actually start, stop, or cancel the time monitoring
    of an activity. This is done actually by the mainwindow.
    """
    sig_btn_start_clicked = QSignal()
    sig_btn_stop_clicked = QSignal()
    sig_btn_cancel_clicked = QSignal()

    def __init__(self, parent=None):
        super().__init__('window', parent)
        self._startfrom = None
        self.__iconsize = 'normal'
        self.setup()

    def setup(self):
        btn_toolbar = self.setup_buttons()
        elap_timer = self.setup_elapsed_timer()

        layout = QGridLayout(self)
        layout.addLayout(btn_toolbar, 0, 0)
        layout.setColumnStretch(0, 100)
        layout.addWidget(elap_timer, 0, 2)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 0, 10)

    def setup_buttons(self):
        """Setup the start, stop, and cancel buttons."""
        btn_start = QToolButtonBase('process_start', self.__iconsize)
        btn_start.setToolTip(
            "<b>Start</b><br><br>"
            "Start monitoring the time elapsed for an activity.<br><br>"
            " The \"Start from\" menu located in the bottom toolbar can be"
            " used to specify a different start time for the activity."
            " The project, tags, and comment for the activity can be specified"
            " in the section below.<br><br>"
            " Note that the project, tags, and comment are saved"
            " to the database only when the button \"Stop\" is clicked."
            " It is thus possible to modify the value of these parameters"
            " while the activity is being monitored."
            )
        btn_start.clicked.connect(lambda: self.sig_btn_start_clicked.emit())

        btn_stop = QToolButtonBase('process_stop', self.__iconsize)
        btn_stop.setToolTip(
            "<b>Stop</b><br><br>"
            "Stop monitoring the time elapsed for the currently running"
            " activity and save it to the database.<br><br>"
            "The activity is saved using the project, tags,"
            " and comment specified in the section below.")
        btn_stop.clicked.connect(lambda: self.sig_btn_stop_clicked.emit())
        btn_stop.setEnabled(False)

        btn_cancel = QToolButtonBase('process_cancel', self.__iconsize)
        btn_cancel.setToolTip(
            "<b>Cancel</b><br><br>"
            "Stop monitoring the time elapsed for the currently running"
            " activity and do NOT add it to the database.")
        btn_cancel.clicked.connect(lambda: self.sig_btn_cancel_clicked.emit())
        btn_cancel.setEnabled(False)

        self.buttons = {'start': btn_start,
                        'stop': btn_stop,
                        'cancel': btn_cancel}

        btn_toolbar = QGridLayout()
        btn_toolbar.setSpacing(3)
        btn_toolbar.setContentsMargins(0, 0, 0, 0)
        btn_toolbar.addWidget(btn_start, 1, 1)
        btn_toolbar.addWidget(btn_stop, 1, 2)
        btn_toolbar.addWidget(btn_cancel, 1, 3)
        btn_toolbar.setRowStretch(0, 100)
        btn_toolbar.setRowStretch(2, 100)
        btn_toolbar.setColumnStretch(4, 100)

        return btn_toolbar

    def setup_elapsed_timer(self):
        """Setup a digital clock to show the elpased time."""
        self.elap_timer = ElapsedTimeLCDNumber()
        self.elap_timer.setToolTip(
            "<b>Elapsed Time</b><br><br>"
            "Time elapsed since the start of the activity currently"
            " being monitored.<br><br>"
            "The reference time used to calculate the elapsed time depends"
            " on the option selected in the \"Start from\" menu located in"
            " the bottom toolbar."
            )
        size_hint = self.elap_timer.sizeHint()
        size_ratio = size_hint.width()/size_hint.height()
        fix_height = self.buttons['start'].style().sizeFromContents(
            QStyle.CT_ToolButton, QStyleOptionToolButton(),
            icons.get_iconsize(self.__iconsize)
            ).height()
        fix_width = fix_height * size_ratio
        self.elap_timer.setFixedSize(fix_width, fix_height)

        return self.elap_timer

    def start(self, startfrom=None):
        """
        Set the state of the buttons and start monitoring the elapsed time
        from the specified startfrom arrow or from arrow.now() if None.
        """
        self.setStartFrom(startfrom)
        self.buttons['start'].setEnabled(False)
        self.buttons['stop'].setEnabled(True)
        self.buttons['cancel'].setEnabled(True)
        self.elap_timer.start(self.startFrom().timestamp)

    def stop(self):
        """
        Set the state of the buttons and stop monitoring the
        elapsed time.
        """
        self.buttons['start'].setEnabled(True)
        self.buttons['stop'].setEnabled(False)
        self.buttons['cancel'].setEnabled(False)
        self.elap_timer.stop()

    def cancel(self):
        """
        Set the state of the buttons, stop monitoring the elapsed time and
        reset the time counter.
        """
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
