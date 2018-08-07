# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Third parties imports

from PyQt5.QtCore import QEvent, QRect, QPoint, Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QDateTimeEdit, QLineEdit, QStyle,
    QStyledItemDelegate, QStyleOptionToolButton, QListView)

# ---- Local imports

from qwatson.utils.dates import qdatetime_from_str
from qwatson.utils import icons
from qwatson.utils.strformating import list_to_str
from qwatson.widgets.tags import TagLineEdit


class BaseDelegate(QStyledItemDelegate):

    def __init__(self, parent):
        super(BaseDelegate, self) .__init__(parent)

    def paint(self, painter, option, index):
        widget = QListView()
        style = widget.style()

        # A row can be highlighted only if the parent tableview is selected.

        if not self.parent().is_selected:
            option.state &= ~QStyle.State_Selected

        # Set the options for mouse hover highlight.

        if self.parent()._hovered_row == index.row():
            option.state |= QStyle.State_MouseOver
        else:
            option.state &= ~QStyle.State_MouseOver

        if index.column() == 0:
            option.viewItemPosition = 1
        elif index.column() == self.parent().model().columnCount()-1:
            option.viewItemPosition = 3
        else:
            option.viewItemPosition = 2

        # Set the options for the text.

        option.text = index.data()
        if index.data(Qt.TextAlignmentRole) & Qt.AlignLeft:
            option.displayAlignment = Qt.AlignLeft | Qt.AlignVCenter
        else:
            option.displayAlignment = Qt.AlignCenter | Qt.AlignVCenter

        # Set the options for the focus rectangle.

        option.state |= QStyle.State_KeyboardFocusChange

        # We fill the background with a solid color before painting the
        # control to override any painting that could have been done by
        # the table view.
        painter.fillRect(option.rect, index.data(Qt.BackgroundRole))

        style.drawControl(QStyle.CE_ItemViewItem, option, painter, widget)


class TagEditDelegate(BaseDelegate):
    """
    A delegate that allow to edit the tags of a frame and
    force an update of the Watson data via the model.
    """
    def __init__(self, parent):
        super(TagEditDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        """Qt method override."""
        self.editor = TagLineEdit(parent)
        return self.editor

    def setEditorData(self, editor, index):
        """Qt method override."""
        editor.set_tags(index.model().get_tags_from_index(index))

    def setModelData(self, editor, model, index):
        """Qt method override."""
        if list_to_str(editor.tags) != model.data(index):
            model.editFrame(index, tags=editor.tags)


class ToolButtonDelegate(BaseDelegate):
    """
    A delegate that draws a tool button in the middle of a table cell that
    emits a signal of the model when clicked.
    """

    def __init__(self, parent):
        super(ToolButtonDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        """Qt method override to prevent the creation of an editor."""
        return None

    def paint(self, painter, option, index):
        """Paint a toolbutton with an icon."""
        super(ToolButtonDelegate, self).paint(painter, option, index)

        opt = QStyleOptionToolButton()
        opt.rect = self.get_btn_rect(option)
        opt.iconSize = icons.get_iconsize('small')
        opt.state |= QStyle.State_Enabled | QStyle.State_Raised
        opt.icon = icons.get_icon('erase-right')

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
            model.emit_btn_delrow_clicked(index)
            return True
        else:
            return super(ToolButtonDelegate, self).editorEvent(
                       event, model, option, index)


class LineEditDelegate(BaseDelegate):
    """
    A delegate that allow to edit the text of a table cell and
    force an update of the Watson data via the model.
    """

    def __init__(self, parent):
        super(LineEditDelegate, self) .__init__(parent)

    def createEditor(self, parent, option, index):
        """Qt method override."""
        self.editor = QLineEdit(parent)
        return self.editor

    def setEditorData(self, editor, index):
        """Qt method override."""
        editor.setText(index.model().data(index))

    def setModelData(self, editor, model, index):
        """Qt method override."""
        if editor.text() != model.data(index):
            model.editFrame(index, message=editor.text())


class ComboBoxDelegate(BaseDelegate):
    """
    A delegate that allow to change the project of an activity from a
    combobox and force an update of the Watson data via the model.
    """

    def __init__(self, parent):
        super(ComboBoxDelegate, self) .__init__(parent)

    def createEditor(self, parent, option, index):
        """Qt method override."""
        return QComboBox(parent)

    def setEditorData(self, editor, index):
        """Qt method override."""
        editor.addItems(index.model().projects)
        editor.setCurrentIndex(
            editor.findText(index.model().get_project_from_index(index)))

    def setModelData(self, editor, model, index):
        """Qt method override."""
        if editor.currentText() != model.data(index):
            model.editFrame(index, project=editor.currentText())


class DateTimeDelegate(BaseDelegate):
    """
    A delegate that allow to edit the time of a table cell and force an
    update of the Watson data via the model.
    """

    def __init__(self, parent):
        super(DateTimeDelegate, self) .__init__(parent)

    def createEditor(self, parent, option, index):
        """Qt method override."""
        self.editor = date_time_edit = QDateTimeEdit(parent)
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
