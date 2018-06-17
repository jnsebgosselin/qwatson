
# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import dateutil

# ---- Third party imports

import arrow

# ---- Local imports

def edit_frame_at(client, index, start=None, stop=None, project=None,
                  message=None, tags=None):
    """
    Edit the frame stored at index in the database from the provided arguments.
    """
    frame = client.frames[index]

    if isinstance(start, str):
        start = arrow.get(start, 'YYYY-MM-DD HH:mm:ss').replace(
            tzinfo=dateutil.tz.tzlocal()).to('utc')
    elif isinstance(start, arrow.Arrow):
        start = start.to('utc')
    else:
        start = frame.start.to('utc')

    if isinstance(stop, str):
        stop = arrow.get(stop, 'YYYY-MM-DD HH:mm:ss').replace(
            tzinfo=dateutil.tz.tzlocal()).to('utc')
    elif isinstance(start, arrow.Arrow):
        stop = stop.to('utc')
    else:
        stop = frame.stop.to('utc')

    project = frame.project if project is None else project
    message = frame.message if message is None else message
    tags = frame.tags if tags is None else tags
    updated_at = arrow.utcnow()

    client.frames[frame.id] = [
        project, start, stop, tags, frame.id, updated_at, message]



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
