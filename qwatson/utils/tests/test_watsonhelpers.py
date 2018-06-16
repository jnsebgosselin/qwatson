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

from qwatson.watson.watson import Watson
from qwatson.utils.watsonhelpers import insert_new_frame
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


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
