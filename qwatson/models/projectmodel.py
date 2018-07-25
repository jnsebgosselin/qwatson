# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

# ---- Third parties imports

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import (QAbstractListModel, QModelIndex, Qt, QVariant)

# ---- Local imports


class WatsonProjectModel(QAbstractListModel):
    sig_model_changed = QSignal()

    def __init__(self, client):
        super(WatsonProjectModel, self).__init__()
        self.client = client

        self.dataChanged.connect(self.model_changed)
        self.rowsInserted.connect(self.model_changed)
        self.modelReset.connect(self.model_changed)
        self.rowsRemoved.connect(self.model_changed)

    def model_changed(self):
        """Emit a signal whenever the model is changed."""
        self.sig_model_changed.emit()

    def rowCount(self, parent=QModelIndex()):
        """Qt method override. Return the number of row of the table."""
        return len(self.client.projects)

    def data(self, index, role=Qt.DisplayRole):
        """Qt method override."""
        if role == Qt.DisplayRole:
            return self.client.projects[index.row()]
        elif role == Qt.ToolTipRole:
            return self.client.projects[index.row()]
        else:
            return QVariant()

    # ---- Utils

    @property
    def projects(self):
        return self.client.projects
