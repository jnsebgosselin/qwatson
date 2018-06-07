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
    """
    A single table view that displays Watson activity log and
    allow sorting and filtering of the data through the use of a proxy model.
    """

    def __init__(self, source_model, parent=None):
        super(BasicWatsonTableView, self).__init__(parent)
        self.setSortingEnabled(False)

        self.proxy_model = WatsonSortFilterProxyModel(source_model)
        self.setModel(self.proxy_model)
        self.proxy_model.sig_btn_delrow_clicked.connect(self.del_model_row)

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

    def del_model_row(self, proxy_index):
        """Delete a row from the model, but ask for confirmation first."""
        frame_id = self.proxy_model.get_frameid_from_index(proxy_index)
        ans = QMessageBox.question(
            self, 'Delete frame', "Do you want to delete frame %s?" % frame_id,
            defaultButton=QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.proxy_model.removeRows(proxy_index)

    def set_date_span(self, date_span):
        """Set the date span in the proxy model."""
        self.proxy_model.set_date_span(date_span)


