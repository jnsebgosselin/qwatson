# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Imports: standard libraries

from time import strptime

# ---- Imports: third parties

from PyQt5.QtCore import QDateTime


def qdatetime_from_str(str_date_time, datetime_format="%Y-%m-%d %H:%M"):
    """Convert a date time str to a QDateTime object."""
    struct_time = strptime(str_date_time, datetime_format)
    return QDateTime(struct_time.tm_year, struct_time.tm_mon,
                     struct_time.tm_mday, struct_time.tm_hour,
                     struct_time.tm_min)
