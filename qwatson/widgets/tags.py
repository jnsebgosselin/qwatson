# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.


# ---- Third party imports

from PyQt5.QtWidgets import QLineEdit


class TagLineEdit(QLineEdit):
    """A lineedit to show and edit tags."""
    def __init__(self, parent=None):
        super(TagLineEdit, self).__init__(parent)

    @property
    def tags(self):
        """Return the list of tags."""
        if self.text() == '':
            return []
        else:
            tags = self.text().split(',')
            return sorted(set(tag.strip() for tag in tags))

    def set_tags(self, tags):
        """Add a the tag list."""
        self.setText(', '.join(tags))
