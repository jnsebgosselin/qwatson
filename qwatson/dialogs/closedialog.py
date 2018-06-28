# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys

# ---- Third party imports

from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtWidgets import (QApplication, QDialogButtonBox,
                             QVBoxLayout, QStyleOption, QPushButton,
                             QAbstractButton)

# ---- Local imports


from qwatson.utils.icons import get_standard_icon, get_standard_iconsize
from qwatson.widgets.layout import InfoBox, ColoredFrame


class CloseDialog(ColoredFrame):
    """
    A dialog to ask the user to stop the time tracker if an activity
    is running when closing.
    """

    def __init__(self, parent=None):
        super(CloseDialog, self).__init__(parent)
        self.set_background_color('light')
        self.main = None
        self.setup()

    # ---- Setup layout

    def setup(self):
        """Setup the dialog widgets and layout."""
        self.button_box = self.setup_dialog_button_box()

        title = "QWatson is currently tracking an activity."
        info = ("Do you want to stop and save the activity before leaving?"
                "<br><br>The activity will be cancelled otherwise.")

        info_box = InfoBox(title, info, 'question', 'messagebox')
        info_box.setContentsMargins(10, 10, 10, 10)

        # Setup the layout of the dialog

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(info_box)
        layout.addWidget(self.button_box)
        layout.setStretch(0, 100)

    def setup_dialog_button_box(self):
        """Setup the buttons of the dialog."""
        self.yes_btn = QPushButton("Yes")
        self.yes_btn.setDefault(True)
        self.no_btn = QPushButton("No")
        self.cancel_btn = QPushButton("Cancel")

        button_box = QDialogButtonBox()
        button_box.addButton(self.yes_btn, QDialogButtonBox.ActionRole)
        button_box.addButton(self.no_btn, QDialogButtonBox.ActionRole)
        button_box.addButton(self.cancel_btn, QDialogButtonBox.ActionRole)
        button_box.clicked.connect(self.receive_answer)
        button_box.layout().setContentsMargins(5, 10, 5, 10)
        button_box.setAutoFillBackground(True)

        color = QStyleOption().palette.window().color()
        palette = button_box.palette()
        palette.setColor(button_box.backgroundRole(), color)
        button_box.setPalette(palette)

        return button_box

    # ---- Bind dialog with main

    def register_dialog_to(self, main):
        """Register the dialog to the main application."""
        if main is not None:
            self.main = main
            self.dialog_index = self.main.addWidget(self)

    def show(self):
        """Qt method override."""
        if self.main is not None:
            self.main.setCurrentIndex(self.dialog_index)
        super(CloseDialog, self).show()

    @QSlot(QAbstractButton)
    def receive_answer(self, button):
        """
        Handle when the dialog question is accepted or canceled by the user.
        """
        if self.main is not None:
            if button == self.yes_btn:
                self.main.btn_startstop.setValue(False)
                self.main.close()
            elif button == self.no_btn:
                self.main.cancel_watson()
                self.main.client.save()
                self.main.close()
            elif button == self.cancel_btn:
                pass
            self.main.setCurrentIndex(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    date_time_dialog = CloseDialog()
    date_time_dialog.show()
    app.exec_()
