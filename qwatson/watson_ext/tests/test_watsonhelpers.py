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
import arrow

# ---- Local imports

from qwatson.utils.dates import local_arrow_from_tuple
from qwatson.watson_ext.watsonextends import Watson
from qwatson.watson_ext.watsonhelpers import (
    round_frame_at, edit_frame_at)
from qwatson.utils.fileio import delete_file_safely

WORKDIR = osp.dirname(__file__)

FIRSTCOMMENT = 'First frame added'
SECONDCOMMENT = 'Second frame added'
THIRDCOMMENT = 'Third frame added'


def test_client_start_stop():
    """Test starting and stopping the client from an empty state."""
    frames_file = osp.join(WORKDIR, 'frames')
    delete_file_safely(frames_file)
    delete_file_safely(frames_file + '.bak')
    assert not osp.exists(frames_file)

    client = Watson(config_dir=WORKDIR)
    assert client.frames_file == frames_file
    assert (len(client.frames)) == 0

    client.start('ci-tests')
    client._current['message'] = FIRSTCOMMENT
    client.stop()
    client.start('ci-tests')
    client._current['message'] = SECONDCOMMENT
    client.stop()
    client.save()

    assert osp.exists(client.frames_file)
    assert (len(client.frames)) == 2


def test_client_frame_insert():
    """Test that inserting a frame works as expected."""
    client = Watson(config_dir=WORKDIR)
    assert len(client.frames) == 2

    client.insert(1, project='ci-tests', start=arrow.now(), stop=arrow.now(),
                  message=THIRDCOMMENT)
    client.save()
    assert len(client.frames) == 3


def test_client_loading_frames():
    """Test that the client saved and loaded the frames correctly."""
    client = Watson(config_dir=WORKDIR)
    assert len(client.frames) == 3
    assert client.frames[0].message == FIRSTCOMMENT
    assert client.frames[1].message == THIRDCOMMENT
    assert client.frames[2].message == SECONDCOMMENT


def test_edit_frame_at():
    client = Watson(config_dir=WORKDIR)

    # Edit first frame.
    start0 = local_arrow_from_tuple((2018, 6, 14, 15, 59, 54))
    stop0 = local_arrow_from_tuple((2018, 6, 14, 16, 34, 25))
    edit_frame_at(client, 0, start=start0, stop=stop0, tags=['edited'])

    frame = client.frames[0]
    assert frame.start.format('YYYY-MM-DD HH:mm:ss') == '2018-06-14 15:59:54'
    assert frame.stop.format('YYYY-MM-DD HH:mm:ss') == '2018-06-14 16:34:25'
    assert client.frames[0].tags == ['edited']

    # Edit second frame.
    start1 = '2018-06-14 16:48:05'
    stop1 = '2018-06-14 17:00:00'
    edit_frame_at(client, 1, start=start1, stop=stop1, tags=['edited'])

    frame = client.frames[1]
    assert frame.start.format('YYYY-MM-DD HH:mm:ss') == start1
    assert frame.stop.format('YYYY-MM-DD HH:mm:ss') == stop1
    assert client.frames[1].tags == ['edited']

    # Edit third frame.
    start2 = '2018-06-14 18:02:57'
    stop2 = '2018-06-14 23:34:25'
    edit_frame_at(client, 2, start=start2, stop=stop2, tags=['edited'])

    frame = client.frames[2]
    assert frame.start.format('YYYY-MM-DD HH:mm:ss') == start2
    assert frame.stop.format('YYYY-MM-DD HH:mm:ss') == stop2
    assert client.frames[2].tags == ['edited']

    client.save()


def test_round_frame_at():
    client = Watson(config_dir=WORKDIR)

    # Round first frame to 1min.
    round_frame_at(client, 0, 1)
    frame = client.frames[0]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 16:00'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 16:34'

    # Round second frame to 5min.
    round_frame_at(client, 1, 5)
    frame = client.frames[1]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 16:50'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 17:00'

    # Round third frame to 10min.
    round_frame_at(client, 2, 10)
    frame = client.frames[2]
    assert frame.start.format('YYYY-MM-DD HH:mm') == '2018-06-14 18:00'
    assert frame.stop.format('YYYY-MM-DD HH:mm') == '2018-06-14 23:30'

    client.save()


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
