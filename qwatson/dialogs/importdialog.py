# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys

# ---- Third party imports

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QPushButton

# ---- Local imports

from qwatson.dialogs.basedialog import BaseDialog
from qwatson.utils import icons
from qwatson.widgets.layout import InfoBox


class ImportDialog(BaseDialog):
    """
    A dialog to ask the user to stop the time tracker if an activity
    is running when closing.
    """

    def __init__(self, main=None, parent=None):
        super(ImportDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)

    # ---- Setup layout

    def setup(self):
        """Setup the dialog widgets and layout."""

        # Add buttons to the dialog

        self.add_dialog_button(QPushButton('Import'), 'Import', True)
        self.add_dialog_button(QPushButton('Cancel'), 'Cancel')

        # Setup the info box

        url_i = "https://github.com/jnsebgosselin/qwatson#installation"
        info_text = (
            "<b>Do you want to import Watson's settings and data?</b><br><br>"
            "For compatibility reasons, QWatson uses separate settings"
            " and data from Watson."
            " See the <a href=\"%s\">documentation</a> for more details."
            ) % url_i

        info_box = InfoBox(info_text, icon=icons.get_icon('master'))
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
            if answer == 'Import':
                self.main.import_data_from_watson()
            else:
                self.main.create_empty_frames_file()
            self.main.setCurrentIndex(0)
            self.main.removeWidget(self)
            self.main.import_dialog = None
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    date_time_dialog = ImportDialog()
    # date_time_dialog.setFixedSize(300, 162)
    date_time_dialog.show()
    app.exec_()
