
# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.


def insert_new_frame(client, data, index):
    """
    Create a new frame from data and insert it in the client databaset at
    the given index using data.

    data = [project, start, stop tags=None, id=None,
            updated_at=None, message=None]
    """
    new_frame = client.frames.new_frame(*data)

    client.frames.changed = True
    client.frames._rows.insert(index, new_frame)
