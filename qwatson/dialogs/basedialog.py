# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports


# ---- Third party imports

from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QDialogButtonBox,
                             QVBoxLayout, QStyleOption, QPushButton,
                             QAbstractButton)

# ---- Local imports

from qwatson.widgets.layout import ColoredFrame


class BaseDialog(ColoredFrame):
    """
    A base class for constructing dialogs that can be added to the stack of
    the main widget.
    """

    def __init__(self, main=None, parent=None):
        super(BaseDialog, self).__init__(color='light', parent=parent)
        self.answer = None
        self.register_dialog_to(main)
        self.button_box = self.setup_dialog_button_box()
        self.buttons = {}
        self.setup()

    # ---- Setup layout

    def setup(self):
        """Setup the dialog widgets and layout."""
        raise NotImplementedError

    def setup_dialog_button_box(self):
        """Setup the dialog button box."""
        button_box = button_box = QDialogButtonBox()
        button_box.clicked.connect(
            lambda button: self.receive_answer(button.objectName()))
        button_box.layout().setContentsMargins(5, 10, 5, 10)
        button_box.setAutoFillBackground(True)

        color = QStyleOption().palette.window().color()
        palette = button_box.palette()
        palette.setColor(button_box.backgroundRole(), color)
        button_box.setPalette(palette)

        return button_box

    def add_dialog_button(self, button, name, default=False,
                          role=QDialogButtonBox.ActionRole):
        """Add a button to the dialog button box."""
        self.button_box.addButton(button, role)
        self.buttons[name] = button
        button.setObjectName(name)
        button.setDefault(default)

    # ---- Bind dialog with main

    def register_dialog_to(self, main):
        """Register the dialog to the main application."""
        self.main = main
        if main is not None:
            self.dialog_index = self.main.addWidget(self)

    def show(self):
        """Qt method override."""
        if self.main is not None:
            self.main.setCurrentIndex(self.dialog_index)
        super(BaseDialog, self).show()

    def receive_answer(self, answer):
        """
        Handle when an answer has been provided to the dialog by the user.
        """
        raise NotImplementedError
