# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys
import os
import os.path as osp
import shutil
import json

# ---- Third party imports

import click
from PyQt5.QtCore import pyqtSlot as QSlot
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QDialogButtonBox,
                             QVBoxLayout, QStyleOption, QPushButton,
                             QAbstractButton)

# ---- Local imports

from qwatson.utils import icons
from qwatson.utils.watsonhelpers import reset_watson
from qwatson.widgets.layout import InfoBox, ColoredFrame


class QWatsonImportMixin(object):
    """
    A mixin for the main QWatson class with the necessary methods to handle
    the import of config and data files from the watson application folder
    to that of QWatson.
    """

    def setup_import_dialog(self):
        """
        Setup a dialog to import data from the watson application folder
        to that of QWatson the first time QWatson is started.
        """
        if not osp.exists(self.client.frames_file):
            watson_frames_exists = osp.exists(osp.join(
                os.environ.get('WATSON_DIR') or click.get_app_dir('watson'),
                'frames'))
            if watson_frames_exists:
                self.import_dialog = ImportDialog(main=self, parent=self)
                self.import_dialog.show()
            else:
                self.create_empty_frames_file()
        else:
            self.import_dialog = None

    def import_data_from_watson(self):
        """
        Copy the relevant resources files from the watson application folder
        to that of QWatson.
        """
        filenames = ['frames', 'frames.bak', 'last_sync', 'state', 'state.bak']
        watson_dir = (os.environ.get('WATSON_DIR') or
                      click.get_app_dir('watson'))
        for filename in filenames:
            shutil.copyfile(osp.join(watson_dir, filename),
                            osp.join(self.client._dir, filename))
        self.reset_model_and_gui()

    def create_empty_frames_file(self):
        """
        Create an empty frame file to indicate that QWatson have been
        started at least one time.
        """
        content = json.dumps({})
        with open(self.client.frames_file, 'w') as f:
            f.write(content)

    def reset_model_and_gui(self):
        """
        Force a reset of the watson client and a refresh of the gui and
        table model.
        """
        reset_watson(self.client)
        self.activity_input_dial.set_projects(self.client.projects)
        if len(self.client.frames) > 0:
            lastframe = self.client.frames[-1]
            self.activity_input_dial.set_current_project(lastframe.project)
            self.activity_input_dial.set_tags(lastframe.tags)
            self.activity_input_dial.set_comment(lastframe.message)
        self.model.modelReset.emit()


class ImportDialog(ColoredFrame):
    """
    A dialog to ask the user to stop the time tracker if an activity
    is running when closing.
    """

    def __init__(self, main=None, parent=None):
        super(ImportDialog, self).__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.set_background_color('light')
        self.setup()
        self.register_dialog_to(main)

    # ---- Setup layout

    def setup(self):
        """Setup the dialog widgets and layout."""
        self.button_box = self.setup_dialog_button_box()

        url_i = "https://github.com/jnsebgosselin/qwatson#installation"
        title = "First time configuration wizard"
        info = ("For compatibility reasons, QWatson uses separate settings"
                " and data from Watson"
                " (see the <a href=\"%s\">documentation</a> for more details)."
                "<br><br>"
                "Do you want to import Watson's settings and data?"
                ) % url_i

        info_box = InfoBox(title, info, icon=icons.get_icon('master'))
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
        self.import_btn = QPushButton("Import")
        self.import_btn.setDefault(True)
        self.cancel_btn = QPushButton("Cancel")

        button_box = QDialogButtonBox()
        button_box.addButton(self.import_btn, QDialogButtonBox.ActionRole)
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
        self.main = main
        if main is not None:
            self.dialog_index = self.main.addWidget(self)

    def show(self):
        """Qt method override."""
        if self.main is not None:
            self.main.setCurrentIndex(self.dialog_index)
        super(ImportDialog, self).show()

    @QSlot(QAbstractButton)
    def receive_answer(self, button):
        """
        Handle when the dialog question is accepted or canceled by the user.
        """
        if self.main is not None:
            if button == self.import_btn:
                self.main.import_data_from_watson()
            else:
                self.main.create_empty_frames_file()
            self.main.setCurrentIndex(0)
            self.main.removeWidget(self)
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    date_time_dialog = ImportDialog()
    # date_time_dialog.setFixedSize(300, 162)
    date_time_dialog.show()
    app.exec_()
