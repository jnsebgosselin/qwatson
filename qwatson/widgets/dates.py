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
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import QApplication, QLabel

# ---- Local imports

from qwatson.utils import icons
from qwatson.utils.dates import arrowspan_to_str
from qwatson.widgets.toolbar import QToolButtonBase, ToolBarWidget


class DateRangeNavigator(ToolBarWidget):
    """A widget to navigate date spans."""

    sig_date_span_changed = QSignal(tuple)

    def __init__(self, icon_size='small', parent=None):
        super(DateRangeNavigator, self).__init__(parent)

        self.home = arrow.now().floor('week').span('week')
        self.current = self.home

        self.setup(icon_size)
        self.setup_date_range_label()

    def setup(self, icon_size):
        """Setup the widget with the provided arguments."""
        self.date_range_labl = QLabel()
        self.btn_home = QToolButtonBase('home')
        self.btn_home.clicked.connect(self.go_home)
        self.btn_next = QToolButtonBase('go-next')
        self.btn_next.clicked.connect(self.go_next_range)
        self.btn_next.setEnabled(False)
        self.btn_prev = QToolButtonBase('go-previous')
        self.btn_prev.clicked.connect(self.go_previous_range)

        # setup the layout

        self.addWidget(self.btn_prev)
        self.addWidget(self.btn_next)
        self.addWidget(self.btn_home)
        self.addWidget(self.date_range_labl)

        self.set_icon_size(icon_size)

    def set_icon_size(self, icon_size):
        """Set the size of the button icon."""
        self.btn_home.setIconSize(icons.get_iconsize(icon_size))
        self.btn_prev.setIconSize(icons.get_iconsize(icon_size))
        self.btn_next.setIconSize(icons.get_iconsize(icon_size))

    def go_next_range(self):
        """Go forward one date range step."""
        self.current = (self.current[0].shift(weeks=1),
                        self.current[1].shift(weeks=1))
        self.setup_date_range_label()
        self.btn_next.setEnabled(self.current != self.home)
        self.sig_date_span_changed.emit(self.current)

    def go_previous_range(self):
        """Go back one date range step."""
        self.current = (self.current[0].shift(weeks=-1),
                        self.current[1].shift(weeks=-1))
        self.setup_date_range_label()
        self.btn_next.setEnabled(self.current != self.home)
        self.sig_date_span_changed.emit(self.current)

    def go_home(self):
        """Go back to the range encompassing the present day."""
        self.current = self.home
        self.btn_next.setEnabled(False)
        self.setup_date_range_label()
        self.sig_date_span_changed.emit(self.current)

    def setup_date_range_label(self):
        """Setup the text in the label widget."""
        self.date_range_labl.setText(arrowspan_to_str(self.current))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    date_range_nav = DateRangeNavigator()
    date_range_nav.show()
    app.exec_()
