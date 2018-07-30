# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys

# ---- Third party imports

from PyQt5.QtWidgets import (QApplication, QVBoxLayout, QPushButton)

# ---- Local imports

from qwatson.dialogs.basedialog import BaseDialog
from qwatson.widgets.layout import InfoBox


class CloseDialog(BaseDialog):
    """
    A dialog to ask the user to stop the time tracker if an activity
    is running when closing.
    """

    def __init__(self, main=None, parent=None):
        super(CloseDialog, self).__init__(main, parent)

    # ---- Setup layout

    def setup(self):
        """Setup the dialog widgets and layout."""

        # Add buttons to the dialog

        self.add_dialog_button(QPushButton('Yes'), 'Yes', True)
        self.add_dialog_button(QPushButton('No'), 'No')
        self.add_dialog_button(QPushButton('Cancel'), 'Cancel')

        # Setup the info box

        info_text = (
            "<b>Do you want to stop and save the current activity before "
            "leaving?</b><br><br>The activity will be cancelled otherwise.")
        info_box = InfoBox(info_text, 'question', 'messagebox')
        info_box.setContentsMargins(10, 10, 10, 10)

        # Setup the layout of the dialog

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(info_box)
        layout.addWidget(self.button_box)
        layout.setStretch(0, 100)

    # ---- Bind dialog with main

    def receive_answer(self, answer):
        """
        Handle when an answer has been provided to the dialog by the user.
        """
        if self.main is not None:
            if answer == 'Yes':
                self.main.stop_watson()
                self.main.close()
            elif answer == 'No':
                self.main.cancel_watson()
                self.main.close()
            elif answer == 'Cancel':
                pass
            self.main.setCurrentIndex(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    date_time_dialog = CloseDialog()
    date_time_dialog.show()
    app.exec_()
