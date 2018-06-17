# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import os
import os.path as osp
from datetime import datetime

# ---- Third party imports

import pytest
import arrow

# ---- Local imports

from qwatson.watson.watson import Watson
from qwatson.utils.watsonhelpers import (insert_new_frame, round_frame_at,
                                         edit_frame_at)
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

    data = ['ci-tests', arrow.now(), arrow.now(), None,
            None, None, THIRDCOMMENT]
    insert_new_frame(client, data, index=1)
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
    start0 = arrow.get(datetime(2018, 6, 14, 15, 59, 54))
    stop0 = arrow.get(datetime(2018, 6, 14, 16, 34, 25))
    edit_frame_at(client, 0, start=start0, stop=stop0, tags=['edited'])
    assert client.frames[0].start == start0
    assert client.frames[0].stop == stop0
    assert client.frames[0].tags == ['edited']

    start1 = arrow.get(datetime(2018, 6, 14, 16, 48, 5))
    stop1 = arrow.get(datetime(2018, 6, 14, 17, 0, 0))
    edit_frame_at(client, 1, start=start1, stop=stop1, tags=['edited'])
    assert client.frames[1].start == start1
    assert client.frames[1].stop == stop1
    assert client.frames[1].tags == ['edited']

    start2 = arrow.get(datetime(2018, 6, 14, 18, 2, 57))
    stop2 = arrow.get(datetime(2018, 6, 14, 23, 34, 25))
    edit_frame_at(client, 2, start=start2, stop=stop2, tags=['edited'])
    assert client.frames[2].start == start2
    assert client.frames[2].stop == stop2
    assert client.frames[2].tags == ['edited']

    client.save()


def test_round_frame_at():
    client = Watson(config_dir=WORKDIR)

    round_frame_at(client, 0, 1)
    assert client.frames[0].start == arrow.get(datetime(2018, 6, 14, 16, 0))
    assert client.frames[0].stop == arrow.get(datetime(2018, 6, 14, 16, 34))

    round_frame_at(client, 1, 5)
    assert client.frames[1].start == arrow.get(datetime(2018, 6, 14, 16, 50))
    assert client.frames[1].stop == arrow.get(datetime(2018, 6, 14, 17, 0))

    round_frame_at(client, 2, 10)
    assert client.frames[2].start == arrow.get(datetime(2018, 6, 14, 18, 0))
    assert client.frames[2].stop == arrow.get(datetime(2018, 6, 14, 23, 30))

    client.save()


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
