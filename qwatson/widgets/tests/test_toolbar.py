# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import os
import os.path as osp

# ---- Third party imports

import pytest
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QMouseEvent

# ---- Local imports

from qwatson.widgets.toolbar import DropDownToolButton


WORKDIR = osp.dirname(__file__)
FRAMEFILE = osp.join(WORKDIR, 'frames')
STATEFILE = osp.join(WORKDIR, 'state')


# ---- Test DropDownToolButton

def test_dropdowntoolbutton(qtbot):
    drop_down_btn = DropDownToolButton(style=('text_beside'))
    drop_down_btn.addItems(['first item', 'second item', 'third item'])

#    qtbot.addWidget(drop_down_btn)
#    qtbot.addWidget(drop_down_btn.droplist)
    drop_down_btn.show()
    qtbot.waitForWindowShown(drop_down_btn)

    # --- Test the button

    assert drop_down_btn.text() == 'first item'
    assert drop_down_btn.currentIndex() == 0

    # Change the button selection programmatically and assert a signal
    # is fired.

    with qtbot.waitSignal(drop_down_btn.sig_item_selected):
        drop_down_btn.setCurrentIndex(2)
    assert drop_down_btn.text() == 'third item'
    assert drop_down_btn.currentIndex() == 2

    # Set programatically a wrong index in the dropdown button.

    with qtbot.waitSignal(drop_down_btn.sig_item_selected):
        drop_down_btn.setCurrentIndex(3)
        assert drop_down_btn.text() == ''
    assert drop_down_btn.currentIndex() == -1

    # --- Test the droplist

    droplist = drop_down_btn.droplist

    # Open the list, clear the focus, and asser the list was closed.

    qtbot.mouseClick(drop_down_btn, Qt.LeftButton)
    qtbot.waitForWindowShown(droplist)
    assert droplist.hasFocus()
    droplist.clearFocus()
    assert not droplist.isVisible()

    # Select a new item in the list and press the Enter key.

    qtbot.mouseClick(drop_down_btn, Qt.LeftButton)
    qtbot.waitForWindowShown(droplist)
    assert droplist.hasFocus()

    with qtbot.waitSignal(droplist.sig_item_selected):
        droplist.setCurrentRow(2)
        qtbot.keyPress(droplist, Qt.Key_Enter)
    assert not droplist.isVisible()

    assert drop_down_btn.text() == 'third item'
    assert drop_down_btn.currentIndex() == 2

    # Select a new item in the list with the mouse.
    qtbot.mouseClick(drop_down_btn, Qt.LeftButton)
    qtbot.waitForWindowShown(droplist)
    assert droplist.hasFocus()
    assert droplist.isVisible()

    visual_rect = droplist.visualItemRect(droplist.item(0))
    with qtbot.waitSignal(droplist.sig_item_selected):
        qtbot.mouseClick(droplist.viewport(), Qt.LeftButton,
                         pos=visual_rect.center())

    assert not droplist.isVisible()
    assert drop_down_btn.text() == 'first item'
    assert drop_down_btn.currentIndex() == 0


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
