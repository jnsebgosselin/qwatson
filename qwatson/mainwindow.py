# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import sys
import platform
from time import strftime, gmtime

# ---- Third parties imports
from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import (Qt, QAbstractTableModel, QVariant, QRect, QPoint,
                          QSize,QEvent, QModelIndex)
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout, QLabel,
                             QTableView, QItemDelegate, QPushButton,
                             QStyleOptionButton, QStyle, QStyledItemDelegate,
                             QStyleOptionToolButton, QStyleOptionViewItem,
                             QHeaderView, QMessageBox, QSizePolicy,
                             QTextEdit)

# ---- Local imports

from qwatson.watson.watson import Watson
from qwatson.utils import icons
from qwatson.widgets.comboboxes import ComboBoxEdit
from qwatson.widgets.clock import ElapsedTimeLCDNumber
from qwatson.widgets.toolbar import (ToolBarWidget, OnOffToolButton,
                                     QToolButtonSmall)
from qwatson import __namever__


class QWatson(QWidget):

    def __init__(self, parent=None):
        super(QWatson, self).__init__(parent)
        self.setWindowIcon(icons.get_icon('master'))
        self.setWindowTitle(__namever__)
        self.setWindowFlags(Qt.Window |
                            Qt.WindowMinimizeButtonHint |
                            Qt.WindowCloseButtonHint)

        if platform.system() == 'Windows':
            import ctypes
            myappid = __namever__
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                myappid)

        self.client = Watson()
        self.model = WatsonTableModel(self.client)

        self.frame_viewer = WatsonTableView(self.model, parent=self)
        self.setup()

    def setup(self):
        """Setup the widget with the provided arguments."""
        timebar = self.setup_timebar()
        self.setup_toolbar()
        self.setup_project_cbox()

        self.msg_textedit = QTextEdit()
        self.msg_textedit.setMaximumHeight(50)
        self.msg_textedit.setSizePolicy(
                QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed))

        layout = QGridLayout(self)
        layout.addWidget(QLabel('Project :'), 0, 0)
        layout.addWidget(self.project_cbox, 0, 1)
        layout.addWidget(self.toolbar, 0, 2)
        layout.addWidget(self.msg_textedit, 1, 0, 1, 3)
        layout.addWidget(timebar, 2, 0, 1, 3)

        layout.setColumnStretch(1, 100)
        layout.setRowStretch(1, 100)

    def setup_project_cbox(self, name=None):
        """
        Setup the list of all the existing projects, sorted by name, in a
        combobox.
        """
        self.project_cbox = ComboBoxEdit()
        self.project_cbox.setFixedHeight(icons.get_iconsize('small').height())

        self.project_cbox.currentIndexChanged.connect(
            self._project_cbox_currentIndexChanged)
        self.project_cbox.sig_item_renamed.connect(self.project_renamed)
        self.project_cbox.sig_item_added.connect(self.new_project_added)

        self.project_cbox.addItems(self.client.projects)
        if len(self.client.frames) > 0:
            self.project_cbox.setCurentText(self.client.frames[-1][2])
        self._project_cbox_currentIndexChanged(
            self.project_cbox.currentIndex())

    def setup_toolbar(self):
        """Setup the main toolbar of the widget"""
        self.toolbar = ToolBarWidget()

        self.btn_add = QToolButtonSmall('plus')
        self.btn_add.clicked.connect(self.btn_add_isclicked)
        self.btn_add.setToolTip("Create a new project")

        self.btn_rename = QToolButtonSmall('edit')
        self.btn_rename.clicked.connect(self.btn_rename_isclicked)
        self.btn_rename.setToolTip("Rename the current project")

        self.btn_del = QToolButtonSmall('clear')
        self.btn_del.clicked.connect(self.btn_del_isclicked)
        self.btn_del.setToolTip("Delete the current project")

        self.btn_report = QToolButtonSmall('note')
        self.btn_report.clicked.connect(self.frame_viewer.show)

        # ---- Populate the toolbar

        items = [self.btn_add, self.btn_rename,
                 self.btn_del, None, self.btn_report]
        for item in items:
            self.toolbar.addWidget(item)

    def setup_timebar(self):
        self.btn_startstop = OnOffToolButton('process_start', 'process_stop')
        self.btn_startstop.setIconSize(icons.get_iconsize('large'))
        self.btn_startstop.setToolTip(
            "Start or stop monitoring time for the given project")
        self.btn_startstop.sig_value_changed.connect(
            self.btn_startstop_isclicked)

        self.elap_timer = ElapsedTimeLCDNumber()
        size_hint = self.elap_timer.sizeHint()
        size_ratio = size_hint.width()/size_hint.height()
        self.elap_timer.setFixedHeight(icons.get_iconsize('large').height())
        self.elap_timer.setMinimumWidth(self.elap_timer.height() * size_ratio)

        # ---- Setup layout

        timebar = QWidget()
        layout = QGridLayout(timebar)
        layout.addWidget(self.btn_startstop, 0, 0)
        layout.addWidget(self.elap_timer, 0, 1)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setColumnStretch(2, 100)

        return timebar

    # ---- Project combobox handlers

    def _project_cbox_currentIndexChanged(self, index):
        self.btn_startstop.setEnabled(index != -1)
        self.btn_rename.setEnabled(index != -1)
        self.btn_del.setEnabled(index != -1)

    def project_renamed(self, old_name, new_name):
        """Handle when a project is renamed in the combobox."""
        self.model.beginResetModel()
        self.client.rename_project(old_name, new_name)
        self.model.endResetModel()

    def new_project_added(self, name):
        """Handle when a new project is added in the combobox."""
        self.btn_startstop.setValue(True)

    # ---- Toolbar handlers

    def btn_startstop_isclicked(self):
        """Handle when the button to start and stop Watson is clicked."""
        if self.btn_startstop.value():
            self.client.start(self.project_cbox.currentText())
            self.elap_timer.start()
        else:
            self.elap_timer.stop()
            self.model.beginInsertRows(QModelIndex(),
                                       len(self.client.frames),
                                       len(self.client.frames))
            self.client._current['message'] = self.msg_textedit.toPlainText()
            self.client.stop()
            self.client.save()
            self.model.endInsertRows()
        self.project_cbox.setEnabled(not self.btn_startstop.value())
        self.btn_add.setEnabled(not self.btn_startstop.value())
        self.btn_rename.setEnabled(not self.btn_startstop.value())
        self.btn_del.setEnabled(not self.btn_startstop.value())

    def btn_add_isclicked(self):
        self.project_cbox.set_edit_mode('add')

    def btn_rename_isclicked(self):
        self.project_cbox.set_edit_mode('rename')

    def btn_del_isclicked(self):
        project = self.project_cbox.currentText()
        index = self.project_cbox.currentIndex()

        msg = ("Do you want to delete project %s and all related frame?"
               ) % project
        ans = QMessageBox.question(self, 'Delete project', msg,
                                   defaultButton=QMessageBox.No)

        if ans == QMessageBox.Yes:
            self.project_cbox.removeItem(index)
            if project in self.client.projects:
                self.model.beginResetModel()
                self.client.delete_project(project)
                self.model.endResetModel()

    def closeEvent(self, event):
        """Qt method override."""
        self.client.save()
        event.accept()


class WatsonTableView(QTableView):
    def __init__(self, model, parent=None, *args):
        super(WatsonTableView, self).__init__()
        self.setWindowIcon(icons.get_icon('master'))
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.setMinimumWidth(650)
        self.setMinimumHeight(500)
        self.setSortingEnabled(False)

        self.setModel(model)
        self.setItemDelegateForColumn(0, ToolButtonDelegate(self))

        self.setColumnWidth(0, icons.get_iconsize('small').width() + 8)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.verticalHeader().hide()

    def setModel(self, model):
        """Qt method override."""
        super(WatsonTableView, self).setModel(model)
        model.sig_btn_delrow_clicked.connect(self.del_model_row)

    def del_model_row(self, index):
        """Delete a row from the model."""
        frame_id = self.model().frames[index.row()].id
        ans = QMessageBox.question(
            self, 'Delete frame', "Do you want to delete frame %s?" % frame_id,
            defaultButton=QMessageBox.No)
        if ans == QMessageBox.Yes:
            self.model().removeRows(index)


class WatsonTableModel(QAbstractTableModel):

    HEADER = ['', 'start', 'end', 'duration', 'project', 'comment', 'id']
    sig_btn_delrow_clicked = QSignal(QModelIndex)

    def __init__(self, client, checked=False):
        super(WatsonTableModel, self).__init__()
        self.client = client
        self.frames = client.frames

    def rowCount(self, x):
        """Qt method override. Return the number of row of the table."""
        return len(self.frames)

    def columnCount(self, x):
        """Qt method override. Return the number of column of the table."""
        return len(self.HEADER)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if index.column() == 1:
                return self.frames[index.row()][0].format('YYYY-MM-DD HH:mm')
            elif index.column() == 2:
                return self.frames[index.row()][1].format('YYYY-MM-DD HH:mm')
            elif index.column() == 3:
                total_seconds = (self.frames[index.row()][1] -
                                 self.frames[index.row()][0]).total_seconds()
                return strftime("%H:%M:%S", gmtime(total_seconds))
            elif index.column() == 4:
                return str(self.frames[index.row()][2])
            elif index.column() == 5:
                msg = self.frames[index.row()].message
                return '' if msg is None else msg
            elif index.column() == 6:
                return self.frames[index.row()].id
            else:
                return ''
        elif role == Qt.TextAlignmentRole:
            if index.column() == 5:
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
        return Qt.ItemIsEnabled

    def removeRows(self, index):
        """Qt method override to remove rows from the model."""
        self.beginRemoveRows(index.parent(), index.row(), index.row())
        frame_id = self.frames[index.row()].id
        del self.client.frames[frame_id]
        self.endRemoveRows()


class ToolButtonDelegate(QStyledItemDelegate):

    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """Qt method override to prevent the creation of an editor."""
        return None

    def paint(self, painter, option, index):
        """Paint a toolbutton with an icon."""
        opt = QStyleOptionToolButton()
        opt.rect = self.get_btn_rect(option)
        opt.icon = icons.get_icon('erase-left')
        opt.iconSize = icons.get_iconsize('small')
        opt.state |= QStyle.State_Enabled | QStyle.State_Raised

        QApplication.style().drawControl(
            QStyle.CE_ToolButtonLabel, opt, painter)

    def get_btn_rect(self, option):
        """Calculate the size and position of the checkbox."""
        bsize = icons.get_iconsize('small')
        x = option.rect.x() + 3
        y = option.rect.y() + option.rect.height()/2 - bsize.height()/2

        return QRect(QPoint(x, y), bsize)

    def editorEvent(self, event, model, option, index):
        """Qt method override."""
        if (event.type() == QEvent.MouseButtonPress
                and event.button() == Qt.LeftButton):
            model.sig_btn_delrow_clicked.emit(index)
            return True
        else:
            return super(ToolButtonDelegate, self).editorEvent(
                       event, model, option, index)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    watson_gui = QWatson()
    watson_gui.show()
    watson_gui.setFixedSize(watson_gui.size())
    app.exec_()
