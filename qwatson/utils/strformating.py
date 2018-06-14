# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.


def list_to_str(tags, start='[', tail=']', sep='] ['):
    """Format a list of string to a single string"""
    if len(tags) == 0 or tags == ['']:
        return ''
    else:
        return start + sep.join(tags) + tail
