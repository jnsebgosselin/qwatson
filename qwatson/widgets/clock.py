# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import time
import sys
import arrow

# ---- Third party imports

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QLCDNumber, QApplication

# https://stackoverflow.com/questions/14478574/
# changing-the-digit-color-of-qlcd-number


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

    def update_elapsed_time(self):
        """Update elapsed time in the widget."""
        self._elapsed_time = time.time() - self._start_time
        self.display(
            time.strftime("%H:%M:%S", time.gmtime(self._elapsed_time)))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    timer = ElapsedTimeLCDNumber()
    timer.show()
    timer.start(arrow.now().timestamp)
    app.exec_()
