# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

# ---- Imports: standard libraries

from time import strptime
import dateutil
from datetime import datetime

# ---- Imports: third parties

import arrow
from PyQt5.QtCore import QDateTime


def total_seconds_to_hour_min(total_seconds):
    """
    Format the total number of seconds to a non-zero-padded str hour-minute
    format with units.
    """
    hours, residual = divmod(total_seconds, 3600)
    minutes = residual // 60
    return "%dh %dmin" % (hours, minutes)


def qdatetime_from_arrow(arrow_datetime):
    """Conver an arrow date time object to a QDateTime object"""
    return QDateTime(arrow_datetime.year, arrow_datetime.month,
                     arrow_datetime.day, arrow_datetime.hour,
                     arrow_datetime.minute)


def qdatetime_from_str(str_date_time, datetime_format="%Y-%m-%d %H:%M"):
    """Convert a date time str to a QDateTime object."""
    struct_time = strptime(str_date_time, datetime_format)
    return QDateTime(struct_time.tm_year, struct_time.tm_mon,
                     struct_time.tm_mday, struct_time.tm_hour,
                     struct_time.tm_min)


def arrowspan_to_str(span):
    """Format an arrow span tuple into a human readable string."""
    start, end = span
    if start.year != end.year:
        date_range_text = "%s %d, %d - %s %d, %d" % (
            arrow.locales.EnglishLocale().month_abbreviation(start.month),
            start.day, start.year,
            arrow.locales.EnglishLocale().month_abbreviation(end.month),
            end.day, end.year)
    elif start.month != end.month:
        date_range_text = "%s %d - %s %d, %d" % (
            arrow.locales.EnglishLocale().month_abbreviation(start.month),
            start.day,
            arrow.locales.EnglishLocale().month_abbreviation(end.month),
            end.day, end.year)
    elif start.day != end.day:
        date_range_text = "%s %d - %d, %d" % (
            arrow.locales.EnglishLocale().month_abbreviation(start.month),
            start.day, end.day, start.year)
        return date_range_text
    else:
        date_range_text = "%s, %s %d %d" % (
            arrow.locales.EnglishLocale().day_name(start.weekday()+1),
            arrow.locales.EnglishLocale().month_abbreviation(start.month),
            start.day, start.year)

    return date_range_text


def round_arrow_to(arrow, base):
    """
    Round a time arrow to the nearest multiple of the specified base in
    minutes.
    """
    deltat = arrow - arrow.floor('hour')
    total_seconds = deltat.total_seconds()
    multiple, residual = divmod(total_seconds, base*60)
    if residual/60 >= base/2:
        multiple += 1
    rounded_arrow = arrow.floor('hour').shift(minutes=multiple*base)

    return rounded_arrow


def contraint_arrow_to_span(arrow, span):
    """Constraint arrow to the limits of the specified span."""
    return min(max(arrow, span[0]), span[1])


def local_arrow_from_tuple(datetime_tuple):
    """
    Return an arrow object from a datetime tuple formatted for local timezone.
    """
    return arrow.get(datetime(*datetime_tuple)
                     ).replace(tzinfo=dateutil.tz.tzlocal())


def local_arrow_from_str(datetime_str, fmt='YYYY-MM-DD HH:mm:ss'):
    """
    Return an arrow object from a string formatted for local timezone.
    """
    return arrow.get(datetime_str, fmt).replace(tzinfo=dateutil.tz.tzlocal())


if __name__ == '__main__':
    datetime_fmt = 'YYYY-MM-DD HH:mm:ss'
    arr1 = arrow.get(datetime(2018, 6, 14, 23, 57, 45))
    print(arr1.format(datetime_fmt))
    print(round_arrow_to(arr1, 1).format(datetime_fmt))
    print(round_arrow_to(arr1, 5).format(datetime_fmt))
    print(round_arrow_to(arr1, 10).format(datetime_fmt))
    print(round_arrow_to(arr1, 30).format(datetime_fmt))
