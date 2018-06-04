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
from PyQt5.QtWidgets import QApplication, QGridLayout, QToolButton, QWidget

# ---- Local imports

from qwatson.utils import icons
from qwatson.widgets.layout import VSep


class ToolBarWidget(QWidget):
    """A standard toolbar with some layout specifics."""
    def __init__(self, parent=None):
        super(ToolBarWidget, self).__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

    def addWidget(self, widget):
        """Add the widget to the toolbar layout."""
        lay = self.layout()
        if widget is None:
            widget = VSep()
        lay.setColumnStretch(lay.columnCount()-1, 0)
        lay.addWidget(widget, 0, lay.columnCount())
        lay.setColumnStretch(lay.columnCount(), 100)


class QToolButtonBase(QToolButton):
    def __init__(self, icon, *args, **kargs):
        super(QToolButtonBase, self).__init__(*args, **kargs)
        icon = icons.get_icon(icon) if isinstance(icon, str) else icon
        self.setIcon(icon)
        self.setAutoRaise(True)
        self.setFocusPolicy(Qt.NoFocus)


class QToolButtonNormal(QToolButtonBase):
    def __init__(self, Qicon, *args, **kargs):
        super(QToolButtonNormal, self).__init__(Qicon, *args, **kargs)
        self.setIconSize(icons.get_iconsize('normal'))


class QToolButtonSmall(QToolButtonBase):
    def __init__(self, Qicon, *args, **kargs):
        super(QToolButtonSmall, self).__init__(Qicon, *args, **kargs)
        self.setIconSize(icons.get_iconsize('small'))


class QToolButtonVRectSmall(QToolButtonBase):
    def __init__(self, Qicon, *args, **kargs):
        super(QToolButtonVRectSmall, self).__init__(Qicon, *args, **kargs)
        self.setIconSize(QSize(8, 20))


class OnOffToolButton(QToolButtonBase):
    """A tool button that can be toggled on or off by clicking on it."""
    sig_value_changed = QSignal(bool)

    def __init__(self, icon, icon_raised=None, size=None, parent=None):
        self._icon = icons.get_icon(icon) if isinstance(icon, str) else icon
        self._icon_raised = (icons.get_icon(icon_raised) if
                             isinstance(icon_raised, str) else icon_raised)
        super(OnOffToolButton, self).__init__(self._icon, parent)
        self.installEventFilter(self)
        if size is not None:
            self.setIconSize(icons.get_iconsize(size))

    def eventFilter(self, widget, event):
        if event.type() == QEvent.MouseButtonPress and self.isEnabled():
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


# %% if __name__ == '__main__'

if __name__ == '__main__':
    app = QApplication(sys.argv)

    onoff_button = OnOffToolButton('play', 'stop')
    onoff_button.setIconSize(icons.get_iconsize('normal'))

    toolbar = ToolBarWidget()
    toolbar.addWidget(onoff_button)
    toolbar.show()

    sys.exit(app.exec_())
