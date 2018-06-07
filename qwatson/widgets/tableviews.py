# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.


# ---- Imports: Third Parties

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtWidgets import QHeaderView, QMessageBox, QTableView

# ---- Local imports

from qwatson.utils import icons
from qwatson.models.tablemodels import WatsonSortFilterProxyModel
from qwatson.models.delegates import (
    ToolButtonDelegate, ComboBoxDelegate, LineEditDelegate, StartDelegate,
    StopDelegate)


# ---- TableView

class BasicWatsonTableView(QTableView):
    """A single table view that displays the Watson data."""

    def __init__(self, model, parent=None):
        super(BasicWatsonTableView, self).__init__(parent)
        self.setSortingEnabled(False)

        proxy_model = WatsonSortFilterProxyModel(model)
        self.setModel(proxy_model)
        proxy_model.sig_btn_delrow_clicked.connect(self.del_model_row)

        # ---- Setup the delegates

        columns = model.COLUMNS

        self.setItemDelegateForColumn(
            columns['icons'], ToolButtonDelegate(self))
        self.setItemDelegateForColumn(
            columns['project'], ComboBoxDelegate(self))
        self.setItemDelegateForColumn(
            columns['comment'], LineEditDelegate(self))
        self.setItemDelegateForColumn(columns['start'], StartDelegate(self))
        self.setItemDelegateForColumn(columns['end'], StopDelegate(self))

        # ---- Setup column size

        self.setColumnWidth(
            columns['icons'], icons.get_iconsize('small').width() + 12)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(
            columns['comment'], QHeaderView.Stretch)
        self.verticalHeader().hide()

    def del_model_row(self, index):
        """Delete a row from the model, but ask for confirmation first."""
        frame_id = self.model().get_frameid_from_index(index)
        ans = QMessageBox.question(
            self, 'Delete frame', "Do you want to delete frame %s?" % frame_id,
            defaultButton=QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.model().removeRows(index)
