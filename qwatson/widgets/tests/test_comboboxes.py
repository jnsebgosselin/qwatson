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
from PyQt5.QtCore import Qt

# ---- Local imports

from qwatson.widgets.comboboxes import ComboBoxEdit


WORKDIR = osp.dirname(__file__)
FRAMEFILE = osp.join(WORKDIR, 'frames')
STATEFILE = osp.join(WORKDIR, 'state')


# ---- Test ComboBoxEdit

def test_comboboxedit_basic(qtbot):
    """Basic tests on the ComboBoxEdit widget."""
    comboboxedit = ComboBoxEdit()

    # Test adding items

    comboboxedit.addItems(['item1', 'item2', 'item3'])
    assert comboboxedit.items() == ['item1', 'item2', 'item3']

    # Test removing items

    comboboxedit.removeItem(4)
    assert comboboxedit.items() == ['item1', 'item2', 'item3']
    comboboxedit.removeItem(1)
    assert comboboxedit.items() == ['item1', 'item3']

    # Test current

    comboboxedit.setCurentText('item3')
    assert comboboxedit.currentIndex() == 1
    comboboxedit.currentText() == 'item3'

    # Test clear items

    comboboxedit.clear()
    assert comboboxedit.items() == []


def test_comboboxedit_edit(qtbot):
    """Test that adding and editing items works as expected."""
    comboboxedit = ComboBoxEdit()
    comboboxedit.show()
    qtbot.addWidget(comboboxedit)
    qtbot.waitForWindowShown(comboboxedit)

    comboboxedit.addItems(['item1', 'item2', 'item3'])
    comboboxedit.setCurentText('item1')

    # Test edit mode None.

    comboboxedit.set_edit_mode('dummy')
    assert not comboboxedit.linedit.isVisible()
    assert comboboxedit.combobox.isVisible()

    # Add an already existing item and press Enter.

    comboboxedit.set_edit_mode('add')
    assert comboboxedit.linedit.isVisible()
    assert not comboboxedit.combobox.isVisible()
    assert comboboxedit.linedit.text() == ''

    qtbot.keyClicks(comboboxedit.linedit, 'item2')
    qtbot.keyPress(comboboxedit.linedit, Qt.Key_Enter)
    assert comboboxedit.items() == ['item1', 'item2', 'item3']
    assert comboboxedit.currentText() == 'item2'
    assert not comboboxedit.linedit.isVisible()
    assert comboboxedit.combobox.isVisible()

    # Add a new item and clear focus.

    comboboxedit.set_edit_mode('add')
    qtbot.keyClicks(comboboxedit.linedit, 'item4')
    comboboxedit.linedit.clearFocus()
    assert comboboxedit.items() == ['item1', 'item2', 'item3', 'item4']
    assert comboboxedit.currentText() == 'item4'
    assert not comboboxedit.linedit.isVisible()
    assert comboboxedit.combobox.isVisible()

    # Cancel the adding of a new item by pressing Escape

    comboboxedit.set_edit_mode('add')
    qtbot.keyClicks(comboboxedit.linedit, 'item5')
    qtbot.keyPress(comboboxedit.linedit, Qt.Key_Escape)
    assert comboboxedit.items() == ['item1', 'item2', 'item3', 'item4']
    assert comboboxedit.currentText() == 'item4'
    assert not comboboxedit.linedit.isVisible()
    assert comboboxedit.combobox.isVisible()

    # Rename an item and press Enter

    comboboxedit.set_edit_mode('rename')
    assert comboboxedit.linedit.text() == 'item4'
    qtbot.keyPress(comboboxedit.linedit, Qt.Key_End)
    qtbot.keyClicks(comboboxedit.linedit, 'b')
    qtbot.keyPress(comboboxedit.linedit, Qt.Key_Enter)
    assert comboboxedit.items() == ['item1', 'item2', 'item3', 'item4b']
    assert comboboxedit.currentText() == 'item4b'
    assert not comboboxedit.linedit.isVisible()
    assert comboboxedit.combobox.isVisible()

    # Rename an item to an already existing item and press Enter

    comboboxedit.set_edit_mode('rename')
    qtbot.keyClicks(comboboxedit.linedit, 'item1')
    qtbot.keyPress(comboboxedit.linedit, Qt.Key_Enter)
    assert comboboxedit.items() == ['item1', 'item2', 'item3']
    assert comboboxedit.currentText() == 'item1'
    assert not comboboxedit.linedit.isVisible()
    assert comboboxedit.combobox.isVisible()


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
