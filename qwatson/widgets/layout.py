# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.


# ---- Third party imports

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QLabel,
                             QScrollArea, QStyleOption, QVBoxLayout)

# ---- Local imports

from qwatson.utils import icons
from qwatson.utils import colors


class HSep(QFrame):
    """An horizontal frame separator."""
    def __init__(self, parent=None):
        super(HSep, self).__init__(parent)
        self.setFrameStyle(52)


class VSep(QFrame):
    """A vertical frame separator."""
    def __init__(self, parent=None):
        super(VSep, self).__init__(parent)
        self.setFrameStyle(53)


class ColoredFrame(QFrame):
    """
    A simple frame widget with utility methods to easily set the color
    of its background.
    """
    def __init__(self, color=None, parent=None):
        super(ColoredFrame, self).__init__(parent)
        self.setAutoFillBackground(True)
        self.set_background_color(color)

    def set_background_color(self, colorname):
        colors.set_widget_palette(self, bgcolor=colorname)


class CollapsableScrollArea(QScrollArea):
    """
    A QScrollArea in which the minimumSizeHint and sizeHint methods have beed
    overriden in order to force the sie hint to respect the minimumHeight
    set by the user.
    """
    def __init__(self, main=None, parent=None):
        super(CollapsableScrollArea, self).__init__(parent)

    def minimumSizeHint(self):
        """
        Qt method override to force the heigth of the minimumSizeHint to the
        minimumHeight of the widget.
        """
        sizehint = QScrollArea.minimumSizeHint(self)
        sizehint.setHeight(self.minimumHeight())
        return sizehint

    def sizeHint(self):
        """
        Qt method override to force the heigth of the sizeHint to the
        minimumHeight of the widget.
        """
        sizehint = QScrollArea.minimumSizeHint(self)
        sizehint.setHeight(self.minimumHeight())
        return sizehint


class InfoBox(ColoredFrame):
    """
    A simple widget with an icon and a text area to display info to the user.
    """
    def __init__(self, info_text='', icon='question', iconsize='messagebox',
                 color='light', parent=None):
        super(InfoBox, self).__init__(parent)
        self.set_background_color(color)

        # Setup the icon.

        icon = (icons.get_standard_icon('SP_MessageBox' + icon.title()) if
                isinstance(icon, str) else icon)
        iconsize = (icons.get_standard_iconsize(iconsize) if
                    isinstance(iconsize, str) else iconsize)

        info_icon = QLabel()
        info_icon.setScaledContents(False)
        info_icon.setPixmap(icon.pixmap(iconsize))

        # Setup the layout for the text.

        self.info_label = info_label = QLabel(info_text)
        info_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        info_label.setWordWrap(True)
        info_label.setOpenExternalLinks(True)

        info_scrollarea = CollapsableScrollArea()
        info_scrollarea.setWidget(info_label)
        info_scrollarea.setWidgetResizable(True)
        info_scrollarea.setMinimumHeight(info_label.minimumHeight())
        info_scrollarea.setFrameStyle(info_scrollarea.NoFrame)

        # Setup the layout of the info box.

        layout = QGridLayout(self)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(15)

        layout.addWidget(info_icon, 0, 0)
        layout.addWidget(info_scrollarea, 0, 1, 2, 1)

        layout.setRowStretch(1, 100)
        layout.setColumnStretch(1, 100)

    def setText(self, text):
        """Set the text of the info box to the specified text."""
        self.info_label.setText(text)

    def setSpacing(self, x):
        """Set the spacing between the icon and the text."""
        self.layout().setSpacing(x)

    def setContentsMargins(self, left, top, right, bottom):
        """Set the content margins values of the info box layout."""
        self.layout().setContentsMargins(left, top, right, bottom)


if __name__ == '__main__':
    import sys
    info_text = ("<b>Lorem Ipsum</b><br><br>"
                 "Lorem ipsum dolor sit amet, consectetur adipiscing elit,"
                 " sed do eiusmod tempor incididunt ut labore et dolore magna"
                 " aliqua. Ut enim ad minim veniam, quis nostrud exercitation"
                 " ullamco laboris nisi ut aliquip ex ea commodo consequat."
                 " Duis aute irure dolor in reprehenderit in voluptate velit"
                 " esse cillum dolore eu fugiat nulla pariatur.<br><br>"
                 " Excepteur sint occaecat cupidatat non proident,"
                 " sunt in culpa qui officia deserunt mollit anim id"
                 " est laborum."
                 )
    app = QApplication(sys.argv)
    date_time_dialog = InfoBox(info_text)
    date_time_dialog.show()
    app.exec_()
