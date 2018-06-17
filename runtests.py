# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

"""
File for running tests programmatically.
"""

import pytest


def main():
    """
    Run pytest tests.
    """
    errno = pytest.main(['-x', 'qwatson',  '-v', '-rw', '--durations=10',
                         '--cov=qwatson'])
    if errno != 0:
        raise SystemExit(errno)


if __name__ == '__main__':
    main()
