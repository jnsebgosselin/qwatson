# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Imports: Standard Libraries

import sys

# ---- Imports: Third Parties

from PyQt5.QtCore import pyqtSignal as QSignal
from PyQt5.QtCore import QSize, Qt, QEvent
from PyQt5.QtWidgets import (QApplication, QToolButton, QMenu, QListWidget,
                             QStyle, QSizePolicy, QStyleOptionToolButton,
                             QHBoxLayout)

# ---- Local imports

from qwatson.utils import icons
from qwatson.widgets.layout import VSep, ColoredFrame


class ToolBarWidget(ColoredFrame):
    """A standard toolbar with some layout specifics."""
    def __init__(self, color=None, parent=None):
        super(ToolBarWidget, self).__init__(color, parent)
        self.widgets = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

    def addWidget(self, widget):
        """Add the widget to the toolbar layout."""
        widget = VSep() if widget is None else widget
        self.widgets.append(widget)
        self.layout().addWidget(widget)

    def addStretch(self, stretch):
        self.layout().addStretch(stretch)

    def setSpacing(self, spacing):
        """Set the spacing between the item of the toolbar."""
        self.layout().setSpacing(spacing)

    def setSizePolicy(self, policy):
        """
        Extend Qt method to set the size policy of all toolbar items also.
        """
        for widget in self.widgets:
            widget.setSizePolicy(policy)
        super().setSizePolicy(policy)


class QToolButtonBase(QToolButton):
    def __init__(self, icon=None, iconsize='normal', parent=None):
        super(QToolButtonBase, self).__init__(parent)
        self.setAutoRaise(True)
        self.setFocusPolicy(Qt.NoFocus)
        if icon is not None:
            self.setIcon(
                icons.get_icon(icon) if isinstance(icon, str) else icon)
            self.setIconSize(
                icons.get_iconsize(iconsize) if isinstance(iconsize, str)
                else iconsize)


class QToolButtonNormal(QToolButtonBase):
    def __init__(self, icon, *args, **kargs):
        super(QToolButtonNormal, self).__init__(icon, 'normal', *args, **kargs)


class QToolButtonSmall(QToolButtonBase):
    def __init__(self, icon, *args, **kargs):
        super(QToolButtonSmall, self).__init__(icon, 'small', *args, **kargs)


class QToolButtonVRectSmall(QToolButtonBase):
    def __init__(self, icon, *args, **kargs):
        super(QToolButtonVRectSmall, self).__init__(icon, QSize(8, 20),
                                                    *args, **kargs)


class OnOffToolButton(QToolButtonBase):
    """A tool button that can be toggled on or off by clicking on it."""
    sig_value_changed = QSignal(bool)

    def __init__(self, icon, icon_raised=None, size='normal', parent=None):
        self._icon = icons.get_icon(icon) if isinstance(icon, str) else icon
        self._icon_raised = (icons.get_icon(icon_raised) if
                             isinstance(icon_raised, str) else icon_raised)
        super(OnOffToolButton, self).__init__(self._icon, size, parent)
        self.installEventFilter(self)

    def eventFilter(self, widget, event):
        if (event.type() == QEvent.MouseButtonRelease and
                self.isEnabled() and
                self.rect().contains(event.pos())):
            self.setValue(not self.value())
        return super(OnOffToolButton, self).eventFilter(widget, event)

    def value(self):
        """Return True if autoRaise is False and False if True."""
        return not self.autoRaise()

    def setValue(self, value, silent=False):
        """Set autoRaise to False if value is True and to True if False."""
        self.setAutoRaise(not bool(value))
        self._setup_icon()
        if not silent:
            self.sig_value_changed.emit(self.value())

    def _setup_icon(self):
        """Setup the icon of the button according to its auto raise state."""
        if self._icon_raised is None:
            return
        icon = self._icon_raised if self.value() else self._icon
        self.setIcon(icon)


class DropDownToolButton(QToolButtonBase):
    """A QToolButton with QComboBox dropdown-like capability."""
    sig_item_selected = QSignal(str)

    def __init__(self, icon=None, iconsize='normal', style='icon_only',
                 parent=None):
        super(DropDownToolButton, self).__init__(icon, iconsize, parent)
        self.set_style(style)

        # Set an empty menu to show the drowdown arrow.
        self.setMenu(QMenu())

        self.droplist = DropDownList(self)
        self.clicked.connect(self.show_dropdown)
        self.droplist.sig_item_selected.connect(self.new_item_selected)

    def set_style(self, style):
        """Set whether text is shown next to the icon or not."""
        self.setToolButtonStyle(
            {'icon_only': Qt.ToolButtonIconOnly,
             'text_only': Qt.ToolButtonTextOnly,
             'text_beside': Qt.ToolButtonTextBesideIcon,
             'text_under': Qt.ToolButtonTextUnderIcon}[style])

    def addItems(self, items):
        """Clear and add items to the button dropdown list."""
        self.droplist.clear()
        self.droplist.addItems(items)
        self.setCurrentIndex(0)

    def currentIndex(self):
        """Return the index of the current item in the dropdown button."""
        return self.droplist.currentRow()

    def setCurrentIndex(self, index):
        """Set the index of the current item in the dropdown button."""
        if index != self.currentIndex():
            self.droplist.setCurrentRow(index)
            current_item = self.droplist.currentItem()
            if current_item is not None:
                self.new_item_selected(current_item.text())
            else:
                self.new_item_selected('')

    def show_dropdown(self):
        """Show and set focus on the dropdown list."""
        self.droplist.show()
        self.droplist.setFocus()

    def new_item_selected(self, text):
        """handle when a new item is selected"""
        self.setText(text)
        self.sig_item_selected.emit(text)


class DropDownList(QListWidget):
    sig_item_selected = QSignal(str)

    def __init__(self, parent):
        super(DropDownList, self).__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.hide()
        self.itemClicked.connect(self.item_is_clicked)

    def show(self):
        """
        Qt method override to show the dropdown list under its parent,
        aligned to its left edge.
        """
        point = self.parent().rect().bottomLeft()
        global_point = self.parent().mapToGlobal(point)
        global_point.setY(global_point.y() + 1)
        self.move(global_point)
        self.resizeColumnsToContents()
        self.resizeHeightToContent()
        super(DropDownList, self).show()

    def resizeColumnsToContents(self):
        """Adjust the width of the list to its content."""
        h = self.sizeHintForColumn(0) + 2*self.frameWidth()
        if self.verticalScrollBar().isVisible():
            h = h + QApplication.style().pixelMetric(QStyle.PM_ScrollBarExtent)
        self.setFixedWidth(h)

    def resizeHeightToContent(self):
        """Set the height of the widget to fit the content."""
        h = 2 * self.frameWidth()
        for i in range(self.count()):
            h += self.sizeHintForRow(i)
        self.setFixedHeight(h)

    def item_is_clicked(self, item):
        """Handle when an item is clicked with the mouse."""
        self.sig_item_selected.emit(self.currentItem().text())
        self.hide()

    def keyPressEvent(self, event):
        """
        Qt method override to select the highlighted item and hide the list
        if the Enter key is pressed.
        """
        super(DropDownList, self).keyPressEvent(event)
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.sig_item_selected.emit(self.currentItem().text())
            self.hide()

    def focusOutEvent(self, event):
        """Qt method override to hide the list when focus is lost."""
        event.ignore()
        # Don't hide it on Mac when main window loses focus because
        # keyboard input is lost
        if sys.platform == "darwin":
            if event.reason() != Qt.ActiveWindowFocusReason:
                self.hide()
        else:
            self.hide()


# %% if __name__ == '__main__'

if __name__ == '__main__':
    app = QApplication(sys.argv)

    drop_down_btn = DropDownToolButton(style=('text_beside'))
    drop_down_btn.setSizePolicy(
        QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
    drop_down_btn.addItems(['round to 1min',
                            'round to 5min',
                            'round to 10min'])

    onoff_button = OnOffToolButton('process_start', 'process_stop', 'normal')

    toolbar = ToolBarWidget()
    toolbar.addStretch(100)
    toolbar.addWidget(onoff_button)
    toolbar.addWidget(drop_down_btn)
    toolbar.addWidget(QToolButtonNormal('home'))
    toolbar.addWidget(None)
    toolbar.addWidget(HistoryNavigationWidget('tiny'))
    toolbar.show()

    size = toolbar.style().sizeFromContents(
        QStyle.CT_ToolButton,
        QStyleOptionToolButton(),
        icons.get_iconsize('normal'))
    print(size)

    sys.exit(app.exec_())
