
# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Third party imports

import arrow

# ---- Local imports

from qwatson.utils.dates import round_arrow_to, local_arrow_from_str


def edit_frame_at(client, index, start=None, stop=None, project=None,
                  message=None, tags=None):
    """
    Edit the frame stored at index in the database from the provided arguments.
    """
    frame = client.frames[index]

    if isinstance(start, str):
    elif start is None:
        start = frame.start
    start = start.to('utc')

    if isinstance(stop, str):
    elif stop is None:
        stop = frame.stop
    stop = stop.to('utc')

    project = frame.project if project is None else project
    message = frame.message if message is None else message
    tags = frame.tags if tags is None else tags
    updated_at = arrow.utcnow()

    client.frames[frame.id] = [
        project, start, stop, tags, frame.id, updated_at, message]


def round_frame_at(client, index, base):
    """Round the start and stop time of the Watson frame at index."""
    frame = client.frames[index]

    start = round_arrow_to(frame.start, base)
    stop = round_arrow_to(frame.stop, base)

    edit_frame_at(client, index, start=start, stop=stop)


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
