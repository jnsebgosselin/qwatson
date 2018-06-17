# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

from time import strftime, gmtime
import datetime

# ---- Third parties imports

import arrow
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import (QAbstractTableModel, QModelIndex,
                          QSortFilterProxyModel, Qt, QVariant)

# ---- Local imports

from qwatson.utils.dates import qdatetime_from_str
from qwatson.utils.strformating import list_to_str
from qwatson.utils.watsonhelpers import edit_frame_at


class WatsonTableModel(QAbstractTableModel):

    HEADER = ['start', 'end', 'duration', 'project',
              'tags', 'comment', 'id', '']
    COLUMNS = {'start': 0, 'end': 1, 'duration': 2, 'project': 3,
               'tags': 4, 'comment': 5, 'id': 6, 'icons': 7}
    EDIT_COLUMNS = [COLUMNS['start'], COLUMNS['end'], COLUMNS['project'],
                    COLUMNS['comment'], COLUMNS['tags']]
    sig_btn_delrow_clicked = QSignal(QModelIndex)
    sig_model_changed = QSignal()
    sig_total_seconds_changed = QSignal(float)

    def __init__(self, client):
        super(WatsonTableModel, self).__init__()
        self.client = client
        self.frames = client.frames

        self.dataChanged.connect(self.model_changed)
        self.rowsInserted.connect(self.model_changed)
        self.modelReset.connect(self.model_changed)
        self.rowsRemoved.connect(self.model_changed)

    def model_changed(self):
        """Emit a signal whenever the model is changed."""
        self.sig_model_changed.emit()

    def rowCount(self, parent=QModelIndex()):
        """Qt method override. Return the number of row of the table."""
        return len(self.frames)

    def columnCount(self, parent=QModelIndex()):
        """Qt method override. Return the number of column of the table."""
        return len(self.HEADER)

    def data(self, index, role=Qt.DisplayRole):
        """Qt method override."""
        if role == Qt.DisplayRole:
            if index.column() == self.COLUMNS['start']:
                return self.frames[index.row()][0].format('YYYY-MM-DD HH:mm')
            elif index.column() == self.COLUMNS['end']:
                return self.frames[index.row()][1].format('YYYY-MM-DD HH:mm')
            elif index.column() == self.COLUMNS['duration']:
                total_seconds = (self.frames[index.row()][1] -
                                 self.frames[index.row()][0]).total_seconds()
                return strftime("%Hh %Mmin", gmtime(total_seconds))
            elif index.column() == self.COLUMNS['project']:
                return str(self.frames[index.row()].project)
            elif index.column() == self.COLUMNS['comment']:
                msg = self.frames[index.row()].message
                return '' if msg is None else msg
            elif index.column() == self.COLUMNS['id']:
                return self.frames[index.row()].id[:7]
            elif index.column() == self.COLUMNS['tags']:
                return list_to_str(self.frames[index.row()].tags)
            else:
                return ''
        elif role == Qt.ToolTipRole:
            if index.column() == self.COLUMNS['comment']:
                msg = self.frames[index.row()].message
                return '' if msg is None else msg
            elif index.column() == self.COLUMNS['id']:
                return self.frames[index.row()].id
            elif index.column() == self.COLUMNS['icons']:
                return "Delete frame"
            elif index.column() == self.COLUMNS['project']:
                return self.frames[index.row()].project
            elif index.column() == self.COLUMNS['tags']:
                return list_to_str(self.frames[index.row()].tags)
        elif role == Qt.TextAlignmentRole:
            if index.column() == self.COLUMNS['comment']:
                return Qt.AlignLeft | Qt.AlignVCenter
            if index.column() == self.COLUMNS['tags']:
                return Qt.AlignLeft | Qt.AlignVCenter
            else:
                return Qt.AlignCenter
        else:
            return QVariant()

    def headerData(self, section, orientation, role):
        """Qt method override."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.HEADER[section]
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return section
        else:
            return QVariant()

    def flags(self, index):
        """Qt method override."""
        if index.column() in self.EDIT_COLUMNS:
            return Qt.ItemIsEnabled | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled

    # ---- Utils

    @property
    def projects(self):
        return self.client.projects

    def get_tags_from_index(self, index):
        """Return a list of tags for the frame from a table index."""
        return self.frames[index.row()].tags

    def get_frameid_from_index(self, index):
        """Return the frame id from a table index."""
        return self.frames[index.row()].id

    def get_start_qdatetime_range(self, index):
        """
        Return QDateTime objects representing the range in which the start
        time of the frame located at index can be moved without creating
        any conflict.
        """
        if index.row() > 0:
            lmin = self.frames[index.row()-1].stop.format('YYYY-MM-DD HH:mm')
        else:
            lmin = '1900-01-01 00:00'
        lmax = self.frames[index.row()].stop.format('YYYY-MM-DD HH:mm')

        return qdatetime_from_str(lmin), qdatetime_from_str(lmax)

    def get_stop_qdatetime_range(self, index):
        """
        Return QDateTime objects representing the range in which the stop
        time of the frame located at index can be moved without creating
        any conflict.
        """
        lmin = self.frames[index.row()].start.format('YYYY-MM-DD HH:mm')
        if index.row() == len(self.frames)-1:
            lmax = arrow.now().format('YYYY-MM-DD HH:mm')
        else:
            lmax = self.frames[index.row()+1].start.format('YYYY-MM-DD HH:mm')

        return qdatetime_from_str(lmin), qdatetime_from_str(lmax)

    # ---- Watson handlers

    def removeRows(self, index):
        """Qt method override to remove rows from the model."""
        self.beginRemoveRows(index.parent(), index.row(), index.row())
        frame_id = self.frames[index.row()].id
        del self.client.frames[frame_id]
        self.endRemoveRows()

    def editFrame(self, index, start=None, stop=None, project=None,
                  message=None, tags=None):
        """
        Edit Frame stored at index in the model from the provided
        arguments
        """
        edit_frame_at(self.client, index.row(), start,
                      stop, project, message, tags)
        self.client.save()
        self.dataChanged.emit(index, index)

    def editDateTime(self, index, date_time):
        """Edit the start or stop field in the frame stored at index."""
        if index.column() == self.COLUMNS['start']:
            self.editFrame(index, start=date_time)
        elif index.column() == self.COLUMNS['end']:
            self.editFrame(index, stop=date_time)


class WatsonSortFilterProxyModel(QSortFilterProxyModel):
    sig_btn_delrow_clicked = QSignal(QModelIndex)
    sig_sourcemodel_changed = QSignal()
    sig_total_seconds_changed = QSignal(float)

    def __init__(self, source_model, date_span=None):
        super(WatsonSortFilterProxyModel, self).__init__()
        self.setSourceModel(source_model)
        self.date_span = date_span
        self.total_seconds = None

        self.sig_btn_delrow_clicked.connect(
            source_model.sig_btn_delrow_clicked.emit)

        source_model.dataChanged.connect(self.source_model_changed)
        source_model.rowsInserted.connect(self.source_model_changed)
        source_model.rowsRemoved.connect(self.source_model_changed)
        source_model.modelReset.connect(self.source_model_changed)

    def source_model_changed(self):
        """Emit a signal whenever the source model changes."""
        self.sig_sourcemodel_changed.emit()
        self.calcul_total_seconds()

    def set_date_span(self, date_span):
        """Set the date span to use to filter the row of the source model."""
        if date_span != self.date_span:
            self.date_span = date_span
            self.invalidateFilter()
            self.calcul_total_seconds()

    def filterAcceptsRow(self, source_row, source_parent):
        """Qt method override."""
        if self.date_span is None:
            return True
        else:
            return self.is_in_date_span(source_row, self.date_span)

    def is_in_date_span(self, source_row, date_span):
        """
        Return whether the start time of the frame stored at the specified
        row of the source model is within the specified date_span.
        """
        frame_start = self.sourceModel().frames[source_row].start
        return (frame_start >= date_span[0] and frame_start < date_span[1])

    def calcul_total_seconds(self):
        """
        Return the total number of seconds of all the activities accepted
        by the proxy model.
        """
        timedelta = datetime.timedelta()
        for i in range(self.rowCount()):
            source_row = self.mapToSource(self.index(i, 0)).row()
            frame = self.sourceModel().frames[source_row]
            timedelta = timedelta + (frame.stop - frame.start)

        total_seconds_old = self.total_seconds
        total_seconds_new = timedelta.total_seconds()
        if total_seconds_new != total_seconds_old:
            self.total_seconds = total_seconds_new
            total_seconds_old = total_seconds_old or 0

            self.sig_total_seconds_changed.emit(self.total_seconds)
            self.sourceModel().sig_total_seconds_changed.emit(
                total_seconds_new - total_seconds_old)

    def get_accepted_row_count(self):
        """Return the number of rows that were accepted by the proxy."""
        return self.rowCount()

    # ---- Map proxy to source

    @property
    def projects(self):
        return self.sourceModel().client.projects

    def get_tags_from_index(self, proxy_index):
        """Return a list of tags for the frame from a table index."""
        return self.sourceModel().get_tags_from_index(
                   self.mapToSource(proxy_index))

    def get_frameid_from_index(self, proxy_index):
        """Return the frame id from a table index."""
        return self.sourceModel().get_frameid_from_index(
                   self.mapToSource(proxy_index))

    def get_start_qdatetime_range(self, proxy_index):
        """Map proxy method to source."""
        return self.sourceModel().get_start_qdatetime_range(
                   self.mapToSource(proxy_index))

    def get_stop_qdatetime_range(self, proxy_index):
        """Map proxy method to source."""
        return self.sourceModel().get_stop_qdatetime_range(
                   self.mapToSource(proxy_index))

    def removeRows(self, proxy_index):
        """Map proxy method to source."""
        self.sourceModel().removeRows(self.mapToSource(proxy_index))

    def editFrame(self, proxy_index, start=None, stop=None, project=None,
                  message=None, tags=None):
        """Map proxy method to source."""
        self.sourceModel().editFrame(
            self.mapToSource(proxy_index), start=start, stop=stop,
            project=project, message=message, tags=tags)

    def editDateTime(self, proxy_index, date_time):
        """Map proxy method to source."""
        self.sourceModel().editDateTime(
            self.mapToSource(proxy_index), date_time)
