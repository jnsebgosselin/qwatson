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


class WatsonTableView(QTableView):
    """A single table view that displays the Watson data."""

    def __init__(self, model, parent=None, *args):
        super(WatsonTableView, self).__init__(parent)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setMinimumWidth(750)
        self.setMinimumHeight(500)
        self.setSortingEnabled(False)

        proxy_model = WatsonSortFilterProxyModel(model)
        self.setModel(proxy_model)

        self.setItemDelegateForColumn(
            model.COLUMNS['icons'], ToolButtonDelegate(self))
        self.setItemDelegateForColumn(
            model.COLUMNS['project'], ComboBoxDelegate(self))
        self.setItemDelegateForColumn(
            model.COLUMNS['comment'], LineEditDelegate(self))
        self.setItemDelegateForColumn(
            model.COLUMNS['start'], StartDelegate(self))
        self.setItemDelegateForColumn(
            model.COLUMNS['end'], StopDelegate(self))

        self.setColumnWidth(
            model.COLUMNS['icons'], icons.get_iconsize('small').width() + 8)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(
            model.COLUMNS['comment'], QHeaderView.Stretch)
        self.verticalHeader().hide()

    def setModel(self, model):
        """Qt method override."""
        super(WatsonTableView, self).setModel(model)
        model.sig_btn_delrow_clicked.connect(self.del_model_row)

    def del_model_row(self, index):
        """Delete a row from the model, but ask for confirmation first."""
        frame_id = self.model().get_frameid_from_index(index)
        ans = QMessageBox.question(
            self, 'Delete frame', "Do you want to delete frame %s?" % frame_id,
            defaultButton=QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.model().removeRows(index)
