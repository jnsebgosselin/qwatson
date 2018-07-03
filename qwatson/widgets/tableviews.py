# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys
from math import ceil

# ---- Third party imports

import arrow
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QGridLayout, QHeaderView, QLabel, QMessageBox, QScrollArea,
    QTableView, QVBoxLayout, QWidget, QFrame)

# ---- Local imports

from qwatson.utils import icons
from qwatson.utils.dates import arrowspan_to_str, total_seconds_to_hour_min
from qwatson.widgets.layout import ColoredFrame
from qwatson.models.tablemodels import WatsonSortFilterProxyModel
from qwatson.models.delegates import (
    ToolButtonDelegate, ComboBoxDelegate, LineEditDelegate, StartDelegate,
    StopDelegate, TagEditDelegate)


# ---- TableWidget

class WatsonDailyTableWidget(QFrame):
    """
    A widget that displays Watson activities on a daily basis over a
    given timespan.
    """

    def __init__(self, model, date_span=arrow.now().floor('week').span('week'),
                 parent=None):
        super(WatsonDailyTableWidget, self).__init__(parent)

        self.total_seconds = 0
        self.date_span = date_span
        self.model = model
        self.model.sig_total_seconds_changed.connect(self.setup_time_total)
        self.tables = []

        self.setup()
        self.set_date_span(date_span)

    def setup(self):
        """Setup the widget with the provided arguments."""
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        scrollarea = self.setup_scrollarea()
        layout.addWidget(scrollarea, 0, 0)

        statusbar = self.setup_satusbar()
        layout.addWidget(statusbar, 1, 0)

    def setup_scrollarea(self):
        """Setup the scrollarea that holds all the table widgets."""
        scrollarea = QScrollArea()

        self.view = ColoredFrame(color='light')

        self.scene = QVBoxLayout(self.view)
        self.scene.addStretch(100)
        self.scene.setSpacing(5)
        self.scene.setContentsMargins(10, 5, 10, 5)

        scrollarea.setMinimumWidth(900)
        scrollarea.setMinimumHeight(500)
        scrollarea.setWidget(self.view)
        scrollarea.setWidgetResizable(True)

        return scrollarea

    def setup_satusbar(self):
        """Setup the statusbar of the table."""
        self.total_time_labl = QLabel()
        self.total_time_labl.setAlignment(Qt.AlignRight)

        font = self.total_time_labl.font()
        font.setBold(True)
        self.total_time_labl.setFont(font)

        return self.total_time_labl

    def set_date_span(self, date_span):
        """
        Set the range over which actitivies are displayed in the widget
        and update the layout accordingly by adding or removing tables.
        """
        total_seconds = round((date_span[1] - date_span[0]).total_seconds())
        ndays = ceil(total_seconds / (60*60*24))
        while True:
            if len(self.tables) == ndays:
                break
            elif len(self.tables) < ndays:
                self.tables.append(WatsonTableWidget(self.model, parent=self))
                self.scene.insertWidget(self.scene.count()-1, self.tables[-1])
            else:
                self.tables.remove(self.tables[-1])
                self.scene.removeWidget(self.tables[-1])
                self.tables[-1].deleteLater()

        base_span = date_span[0].span('day')
        for i, table in enumerate(self.tables):
            table.set_date_span(
                (base_span[0].shift(days=i), base_span[1].shift(days=i)))

    def setup_time_total(self, delta_seconds):
        """
        Setup the total amount of time for all the activities listed
        for the date span.
        """
        self.total_seconds = self.total_seconds + delta_seconds
        self.total_time_labl.setText(
            "Total : %s" % total_seconds_to_hour_min(self.total_seconds))


class WatsonTableWidget(QWidget):
    """
    A widget that contains a formatted table view and a custom title bar
    that shows the date span and the time count of all the activities listed
    in the table.
    """

    def __init__(self, model, parent=None):
        super(WatsonTableWidget, self).__init__(parent)
        self.view = FormatedWatsonTableView(model)
        titlebar = self.setup_titlebar()

        layout = QGridLayout(self)
        layout.addWidget(titlebar, 0, 0)
        layout.addWidget(self.view, 1, 0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.view.proxy_model.sig_total_seconds_changed.connect(
            self.setup_timecount)

    def setup_titlebar(self):
        """Setup the titlebar of the table."""
        font = QLabel().font()
        font.setBold(True)

        self.title = QLabel()
        self.title.setMargin(5)
        self.title.setFont(font)

        self.timecount = QLabel()
        self.timecount.setMargin(5)
        self.timecount.setFont(font)

        titlebar = ColoredFrame(color='grey')
        titlebar_layout = QHBoxLayout(titlebar)
        titlebar_layout.setContentsMargins(0, 0, 0, 0)

        titlebar_layout.addWidget(self.title)
        titlebar_layout.addStretch(100)
        titlebar_layout.addWidget(self.timecount)

        return titlebar

    @property
    def date_span(self):
        """Return the arrow span of the filter proxy model."""
        return self.view.proxy_model.date_span

    def set_date_span(self, date_span):
        """Set the date span in the table and title."""
        self.view.set_date_span(date_span)
        self.title.setText(arrowspan_to_str(date_span))

    def setup_timecount(self, total_seconds):
        """
        Setup the time count for the activities of the table in the titlebar.
        """
        self.timecount.setText(total_seconds_to_hour_min(total_seconds))


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

        columns = source_model.COLUMNS
        self.setItemDelegateForColumn(
            columns['icons'], ToolButtonDelegate(self))
        self.setItemDelegateForColumn(
            columns['project'], ComboBoxDelegate(self))
        self.setItemDelegateForColumn(
            columns['comment'], LineEditDelegate(self))
        self.setItemDelegateForColumn(columns['start'], StartDelegate(self))
        self.setItemDelegateForColumn(columns['end'], StopDelegate(self))
        self.setItemDelegateForColumn(columns['tags'], TagEditDelegate(self))

        # ---- Setup column size

        self.setColumnWidth(columns['tags'],
                            1.5 * self.horizontalHeader().defaultSectionSize())
        self.setColumnWidth(columns['icons'],
                            icons.get_iconsize('small').width() + 12)
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


class FormatedWatsonTableView(BasicWatsonTableView):
    """
    A BasicWatsonTableView formatted to look good when put in a scrollarea
    in a vertical stack of tables.
    """

    def __init__(self, source_model, parent=None):
        super(FormatedWatsonTableView, self).__init__(source_model, parent)
        self.setup()
        self.update_table_height()

    def setup(self):
        """Setup the table view with the provided arguments."""
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setFrameShape(QFrame.NoFrame)
        self.setWordWrap(False)

        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.proxy_model.sig_sourcemodel_changed.connect(
            self.update_table_height)

    def update_table_height(self):
        """
        Update the height of the table to fit all the data, so that there is
        no need for a vertical scrollbar.
        """
        self.setFixedHeight(self.get_min_height())

    def get_min_height(self):
        """Calculate the height of the table content."""
        h = 2 * self.frameWidth()
        for i in range(self.model().get_accepted_row_count()):
            h += self.rowHeight(i)
        return h

    def set_date_span(self, date_span):
        """
        Method override to update table height when setting the date span.
        """
        super(FormatedWatsonTableView, self).set_date_span(date_span)
        self.update_table_height()


if __name__ == '__main__':
    from qwatson.watson.watson import Watson
    from qwatson.models.tablemodels import WatsonTableModel

    client = Watson()
    model = WatsonTableModel(client)

    app = QApplication(sys.argv)
    date_range_nav = WatsonDailyTableWidget(model)
    date_range_nav.show()
    app.exec_()
