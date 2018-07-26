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


class DelProjectDialog(BaseDialog):
    """
    A dialog to ask the user to confirm that he truly wants to delete the
    project and all related frames.
    The QWatson main is actually in charge of deleting the project.
    """

    def __init__(self, main=None, parent=None):
        super(DelProjectDialog, self).__init__(main, parent)

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

    def show(self, project, na):
        """
        Extend show method to update the text of the info box with the
        provided arguments.
        """
        self.project = project

        text = "<b>"
        text += ("All activities that are not in a project "
                 if project == '' else
                 "The project \"%s\" and all related activities " % project)
        text += "will be permanently erased from the database.</b><br><br>"
        text += "%d " % na
        text += 'activity is' if na <= 1 else 'activities are'
        text += (" not currently in a project" if project == '' else
                 " currently in project \"%s\"" % project)
        text += "."
        self.info_box.setText(text)

        super(DelProjectDialog, self).show()

    def receive_answer(self, answer):
        """
        Handle when an answer has been provided to the dialog by the user.
        """
        if self.main is not None:
            if answer == 'Ok':
                self.main.del_project(self.project, force=True)
            elif answer == 'Cancel':
                pass
            self.main.setCurrentIndex(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    d1 = DelProjectDialog()
    d1.show('', 24)
    d1.setFixedSize(300, 162)
    d2 = DelProjectDialog()
    d2.show('x', 35)
    d2.setFixedSize(300, 162)
    app.exec_()
