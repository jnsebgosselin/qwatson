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

from qwatson.utils import colors
from qwatson.utils.dates import local_arrow_from_str, contraint_arrow_to_span
from qwatson.utils.strformating import list_to_str
from qwatson.watson_ext.watsonhelpers import edit_frame_at


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

        self.dataChanged.connect(self.model_changed)
        self.rowsInserted.connect(self.model_changed)
        self.modelReset.connect(self.model_changed)
        self.rowsRemoved.connect(self.model_changed)

    def model_changed(self):
        """Emit a signal whenever the model is changed."""
        self.sig_model_changed.emit()

    def rowCount(self, parent=QModelIndex()):
        """Qt method override. Return the number of row of the table."""
        return len(self.client.frames)

    def columnCount(self, parent=QModelIndex()):
        """Qt method override. Return the number of column of the table."""
        return len(self.HEADER)

    def data(self, index, role=Qt.DisplayRole):
        """Qt method override."""
        frames = self.client.frames
        if role == Qt.DisplayRole:
            if index.column() == self.COLUMNS['start']:
                return frames[index.row()][0].format('YYYY-MM-DD HH:mm')
            elif index.column() == self.COLUMNS['end']:
                return frames[index.row()][1].format('YYYY-MM-DD HH:mm')
            elif index.column() == self.COLUMNS['duration']:
                total_seconds = (frames[index.row()][1] -
                                 frames[index.row()][0]).total_seconds()
                return strftime("%Hh %Mmin", gmtime(total_seconds))
            elif index.column() == self.COLUMNS['project']:
                return str(frames[index.row()].project)
            elif index.column() == self.COLUMNS['comment']:
                msg = frames[index.row()].message
                return '' if msg is None else msg
            elif index.column() == self.COLUMNS['id']:
                return frames[index.row()].id[:7]
            elif index.column() == self.COLUMNS['tags']:
                return list_to_str(frames[index.row()].tags)
            else:
                return ''
        elif role == Qt.ToolTipRole:
            if index.column() == self.COLUMNS['comment']:
                msg = frames[index.row()].message
                return '' if msg is None else msg
            elif index.column() == self.COLUMNS['id']:
                return frames[index.row()].id
            elif index.column() == self.COLUMNS['icons']:
                return "Delete frame"
            elif index.column() == self.COLUMNS['project']:
                return frames[index.row()].project
            elif index.column() == self.COLUMNS['tags']:
                return list_to_str(frames[index.row()].tags)
        elif role == Qt.BackgroundRole:
            return colors.get_qcolor('base')
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
            return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # ---- Utils

    @property
    def projects(self):
        return self.client.projects

    def get_frame_from_index(self, index):
        """Return the frame stored at the row of index."""
        return self.client.frames[index.row()]

    def get_project_from_index(self, index):
        """Return the project of the frame corresponding to the model index."""
        return self.client.frames[index.row()].project

    def get_tags_from_index(self, index):
        """Return a list of tags for the frame from a table index."""
        return self.client.frames[index.row()].tags

    def get_frameid_from_index(self, index):
        """Return the frame id from a table index."""
        return self.client.frames[index.row()].id

    def get_start_datetime_range(self, index):
        """
        Return the range in which the start time of the frame located at
        index can be moved without creating any conflict.
        """
        frames = self.client.frames
        lmin = (frames[index.row()-1].stop if index.row() > 0 else
                local_arrow_from_str('1980-01-01 00:00:00',
                                     'YYYY-MM-DD HH:mm:ss')
                )
        lmax = frames[index.row()].stop
        return lmin, lmax

    def get_stop_datetime_range(self, index):
        """
        Return the range in which the stop time of the frame located at
        index can be moved without creating any conflict.
        """
        frames = self.client.frames
        lmin = frames[index.row()].start
        lmax = (arrow.now() if index.row() == (len(frames)-1) else
                frames[index.row()+1].start)
        return lmin, lmax

    # ---- Watson handlers

    def emit_btn_delrow_clicked(self, index):
        """
        Send a signal with the model index where the button to delete an
        activity has been clicked.
        """
        self.sig_btn_delrow_clicked.emit(index)

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
        date_time = local_arrow_from_str(date_time, 'YYYY-MM-DD HH:mm:ss')
        if index.column() == self.COLUMNS['start']:
            span = self.get_start_datetime_range(index)
            self.editFrame(
                index, start=contraint_arrow_to_span(date_time, span))
        elif index.column() == self.COLUMNS['end']:
            span = self.get_stop_datetime_range(index)
            self.editFrame(
                index, stop=contraint_arrow_to_span(date_time, span))


class WatsonSortFilterProxyModel(QSortFilterProxyModel):
    sig_sourcemodel_changed = QSignal()
    sig_total_seconds_changed = QSignal(float)

    def __init__(self, source_model, date_span=None):
        super(WatsonSortFilterProxyModel, self).__init__()
        self.setSourceModel(source_model)
        self.date_span = date_span
        self.total_seconds = None
        self.project_filters = None
        self.tag_filters = None

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

    def set_project_filters(self, project_filters):
        """
        Set the list of project for which activies are shown in the table.
        """
        if project_filters != self.project_filters:
            self.project_filters = project_filters
            self.invalidateFilter()
            self.calcul_total_seconds()

    def set_tag_filters(self, tag_filters):
        """
        Set the list of tags for which activies are shown in the table.
        """
        if tag_filters != self.tag_filters:
            self.tag_filters = tag_filters
            self.invalidateFilter()
            self.calcul_total_seconds()

    def filterAcceptsRow(self, source_row, source_parent):
        """Qt method override."""
        if self.project_filters is not None:
            project = self.sourceModel().client.frames[source_row].project
            if not self.project_filters.get(project, True):
                return False
        if self.tag_filters is not None:
            tags = self.sourceModel().client.frames[source_row].tags or ['']
            if not any([self.tag_filters.get(tag, True) for tag in tags]):
                return False
        if self.date_span is None:
            return True
        else:
            return self.is_in_date_span(source_row, self.date_span)

    def is_in_date_span(self, source_row, date_span):
        """
        Return whether the start time of the frame stored at the specified
        row of the source model is within the specified date_span.
        """
        frame_start = self.sourceModel().client.frames[source_row].start
        return (frame_start >= date_span[0] and frame_start <= date_span[1])

    def calcul_total_seconds(self):
        """
        Return the total number of seconds of all the activities accepted
        by the proxy model.
        """
        timedelta = datetime.timedelta()
        for i in range(self.rowCount()):
            source_row = self.mapToSource(self.index(i, 0)).row()
            frame = self.sourceModel().client.frames[source_row]
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

    def get_frame_from_index(self, proxy_index):
        """Return the frame stored at the row of index."""
        return self.sourceModel().get_frame_from_index(
                   self.mapToSource(proxy_index))

    def get_project_from_index(self, proxy_index):
        """Return the project of the frame corresponding to the model index."""
        return self.sourceModel().get_project_from_index(
                   self.mapToSource(proxy_index))

    def get_tags_from_index(self, proxy_index):
        """Return a list of tags for the frame from a table index."""
        return self.sourceModel().get_tags_from_index(
                   self.mapToSource(proxy_index))

    def get_frameid_from_index(self, proxy_index):
        """Return the frame id from a table index."""
        return self.sourceModel().get_frameid_from_index(
                   self.mapToSource(proxy_index))

    def emit_btn_delrow_clicked(self, proxy_index):
        """
        Send a signal via the source model with the model index where the
        button to delete an activity has been clicked.
        """
        self.sourceModel().emit_btn_delrow_clicked(
            self.mapToSource(proxy_index))

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
