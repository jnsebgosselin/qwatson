# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Third parties imports

from PyQt5.QtCore import (QEvent, QRect, QPoint, Qt)
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QDateTimeEdit, QLineEdit, QStyle,
    QStyledItemDelegate, QStyleOptionToolButton)

# ---- Local imports

from qwatson.utils.dates import qdatetime_from_str
from qwatson.utils import icons
from qwatson.utils.strformating import list_to_str
from qwatson.widgets.projects_and_tags import TagLineEdit


class TagEditDelegate(QStyledItemDelegate):
    """
    A delegate that allow to edit the tags of a frame and
    force an update of the Watson data via the model.
    """
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """Qt method override."""
        return TagLineEdit(parent)

    def setEditorData(self, editor, index):
        """Qt method override."""
        editor.set_tags(index.model().get_tags_from_index(index))

    def setModelData(self, editor, model, index):
        """Qt method override."""
        if list_to_str(editor.tags) != model.data(index):
            model.editFrame(index, tags=editor.tags)


class ToolButtonDelegate(QStyledItemDelegate):
    """
    A delegate that draws a tool button in the middle of a table cell that
    emits a signal of the model when clicked.
    """

    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """Qt method override to prevent the creation of an editor."""
        return None

    def paint(self, painter, option, index):
        """Paint a toolbutton with an icon."""
        opt = QStyleOptionToolButton()
        opt.rect = self.get_btn_rect(option)
        opt.icon = icons.get_icon('erase-right')
        opt.iconSize = icons.get_iconsize('small')
        opt.state |= QStyle.State_Enabled | QStyle.State_Raised

        QApplication.style().drawControl(
            QStyle.CE_ToolButtonLabel, opt, painter)

    def get_btn_rect(self, option):
        """Calculate the size and position of the checkbox."""
        bsize = icons.get_iconsize('small')
        x = option.rect.x() + option.rect.width()/2 - bsize.width()/2
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


class LineEditDelegate(QStyledItemDelegate):
    """
    A delegate that allow to edit the text of a table cell and
    force an update of the Watson data via the model.
    """

    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """Qt method override."""
        return QLineEdit(parent)

    def setEditorData(self, editor, index):
        """Qt method override."""
        editor.setText(index.model().data(index))

    def setModelData(self, editor, model, index):
        """Qt method override."""
        if editor.text() != model.data(index):
            model.editFrame(index, message=editor.text())


class ComboBoxDelegate(QStyledItemDelegate):
    """
    A delegate that allow to change the project of an activity from a
    combobox and force an update of the Watson data via the model.
    """

    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """Qt method override."""
        return QComboBox(parent)

    def setEditorData(self, editor, index):
        """Qt method override."""
        editor.addItems(index.model().projects)
        editor.setCurrentIndex(editor.findText(index.model().data(index)))

    def setModelData(self, editor, model, index):
        """Qt method override."""
        if editor.currentText() != model.data(index):
            model.editFrame(index, project=editor.currentText())


class DateTimeDelegate(QStyledItemDelegate):
    """
    A delegate that allow to edit the time of a table cell and force an
    update of the Watson data via the model.
    """

    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """Qt method override."""
        date_time_edit = QDateTimeEdit(parent)
        date_time_edit.setCalendarPopup(True)
        date_time_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        return date_time_edit

    def setEditorData(self, editor, index):
        """Qt method override."""
        editor.setDateTime(qdatetime_from_str(index.model().data(index)))

    def setModelData(self, editor, model, index):
        """Qt method override."""
        date_time = editor.dateTime().toString("yyyy-MM-dd hh:mm")
        if date_time != model.data(index):
            model.editDateTime(index, date_time+':00')


class StartDelegate(DateTimeDelegate):
    """
    A delegate that allow to edit the start time of an activity and force an
    update of the Watson data via the model.
    """

    def setEditorData(self, editor, index):
        """Constraint the range of possible values to avoid conflict."""
        super(StartDelegate, self).setEditorData(editor, index)
        qdatetime_range = index.model().get_start_qdatetime_range(index)
        editor.setDateTimeRange(*qdatetime_range)


class StopDelegate(DateTimeDelegate):
    """
    A delegate that allow to edit the stop time of an activity and force an
    update of the Watson data via the model.
    """

    def setEditorData(self, editor, index):
        """Constraint the range of possible values to avoid conflict."""
        super(StopDelegate, self).setEditorData(editor, index)
        qdatetime_range = index.model().get_stop_qdatetime_range(index)
        editor.setDateTimeRange(*qdatetime_range)
