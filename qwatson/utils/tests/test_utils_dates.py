# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Standard imports

import os
from datetime import datetime

# ---- Third party imports

import pytest
import arrow

# ---- Local imports

from qwatson.utils.dates import round_arrow_to


def test_round_arrow_to():
    """
    Assert that the function to round times to the nearest values of
    a given minutes integer is working properly.
    """
    fmt = 'YYYY-MM-DD HH:mm:ss'

    arr1 = arrow.get(datetime(2018, 6, 14, 23, 59, 45))
    assert arr1.format(fmt) == "2018-06-14 23:59:45"
    assert round_arrow_to(arr1, 1).format(fmt) == "2018-06-15 00:00:00"
    assert round_arrow_to(arr1, 5).format(fmt) == "2018-06-15 00:00:00"
    assert round_arrow_to(arr1, 10).format(fmt) == "2018-06-15 00:00:00"
    assert round_arrow_to(arr1, 30).format(fmt) == "2018-06-15 00:00:00"

    arr2 = arrow.get(datetime(2018, 6, 14, 0, 6, 15))
    assert arr2.format(fmt) == "2018-06-14 00:06:15"
    assert round_arrow_to(arr2, 1).format(fmt) == "2018-06-14 00:06:00"
    assert round_arrow_to(arr2, 5).format(fmt) == "2018-06-14 00:05:00"
    assert round_arrow_to(arr2, 10).format(fmt) == "2018-06-14 00:10:00"
    assert round_arrow_to(arr2, 30).format(fmt) == "2018-06-14 00:00:00"

    arr3 = arrow.get(datetime(2018, 6, 14, 4, 23, 58))
    assert arr3.format(fmt) == "2018-06-14 04:23:58"
    assert round_arrow_to(arr3, 1).format(fmt) == "2018-06-14 04:24:00"
    assert round_arrow_to(arr3, 5).format(fmt) == "2018-06-14 04:25:00"
    assert round_arrow_to(arr3, 10).format(fmt) == "2018-06-14 04:20:00"
    assert round_arrow_to(arr3, 30).format(fmt) == "2018-06-14 04:30:00"


if __name__ == "__main__":
    pytest.main(['-x', os.path.basename(__file__), '-v', '-rw'])
