
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
        start = local_arrow_from_str(start, 'YYYY-MM-DD HH:mm:ss')
    elif start is None:
        start = frame.start
    start = start.to('utc')

    if isinstance(stop, str):
        stop = local_arrow_from_str(stop, 'YYYY-MM-DD HH:mm:ss')
    elif stop is None:
        stop = frame.stop
    stop = stop.to('utc')

    project = frame.project if project is None else project
    message = frame.message if message is None else message
    tags = frame.tags if tags is None else tags
    updated_at = arrow.utcnow()

    client.frames[frame.id] = [
        project, start, stop, tags, frame.id, updated_at, message]


def get_frame_nbr_for_project(client, project):
    """Return the number of activities associated with a given project."""
    return len(list(client.frames.filter(projects=[project])))


def round_frame_at(client, index, base):
    """Round the start and stop time of the Watson frame at index."""
    frame = client.frames[index]

    start = round_arrow_to(frame.start, base)
    stop = round_arrow_to(frame.stop, base)

    edit_frame_at(client, index, start=start, stop=stop)


def find_where_to_insert_new_frame(client, new_start, where='above'):
    """
    Return the frame index where to insert a new frame according to its
    start datetime.
    """
    for i, frame in enumerate(client.frames):
        if where == 'above' and new_start <= frame.start:
            return i
        elif where == 'below' and new_start < frame.stop:
            return i
    else:
        return len(client.frames)


def reset_watson(client):
    """
    Reset the internal variables of the client to None to force a reloading
    of the data from the files.
    """
    client._projects = None
    client._current = None
    client._old_state = None
    client._frames = None
    client._last_sync = None
    client._config = None
    client._config_changed = False
