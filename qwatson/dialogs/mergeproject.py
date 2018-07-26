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


class MergeProjectDialog(BaseDialog):
    """
    A dialog to ask the user to confirm that he truly wants to merge project
    x with project y.
    The QWatson main window is actually in charge of deleting the project.
    """

    def __init__(self, main=None, parent=None):
        super(MergeProjectDialog, self).__init__(main, parent)

    # ---- Setup layout

    def setup(self):
        """Setup the dialog widgets and layout."""

        # Add buttons to the dialog

        self.add_dialog_button(QPushButton('Ok'), 'Ok')
        self.add_dialog_button(QPushButton('Cancel'), 'Cancel', True)

        # Setup the info box

        self.info_box = InfoBox('', 'warning', 'messagebox')
        self.info_box.setContentsMargins(10, 10, 10, 10)

        # Setup the layout of the dialog

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.info_box)
        layout.addWidget(self.button_box)
        layout.setStretch(0, 100)

    def show(self, proj1, na1, proj2, na2):
        """
        Extend show method to update the text of the info box with the
        provided arguments.
        """
        self.proj1, self.proj2 = proj1, proj2

        text = "<b>All activities "
        text += ("that are not currently in a project" if proj1 == '' else
                 "of project \"%s\"" % proj1)
        text += " will be permanently merged "
        text += ("with those that are not currently in a project"
                 if proj2 == '' else
                 "with those of project \"%s\"" % proj2)
        text += ".</b><br><br>"
        text += "%d " % na1
        text += 'activity is' if na1 <= 1 else 'activities are'
        text += (" not currently in a project" if proj1 == '' else
                 " currently in project \"%s\"" % proj1)
        text += " and "
        text += "%d " % na2
        text += 'activity is' if na2 <= 1 else 'activities are'
        text += (" not currently in a project" if proj2 == '' else
                 " currently in project \"%s\"" % proj2)
        text += "."
        self.info_box.setText(text)

        super(MergeProjectDialog, self).show()

    def receive_answer(self, answer):
        """
        Handle when an answer has been provided to the dialog by the user.
        """
        if self.main is not None:
            if answer == 'Ok':
                self.main.rename_project(self.proj1, self.proj2, force=True)
            elif answer == 'Cancel':
                pass
            self.main.setCurrentIndex(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    d1 = MergeProjectDialog()
    d1.show('', 3, 'x', 24)
    d1.setFixedSize(300, 162)

    d2 = MergeProjectDialog()
    d2.show('x', 1, 'y', 4)
    d2.setFixedSize(300, 162)

    d3 = MergeProjectDialog()
    d3.show('x', 27, '', 4)
    d3.setFixedSize(300, 162)

    app.exec_()
