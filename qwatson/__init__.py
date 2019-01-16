# -*- coding: utf-8 -*-

"""
QWatson License Agreement (GNU-GPLv3)
--------------------------------------

Copyright (c) 2018 Jean-Sébastien Gosselin
https://github.com/jnsebgosselin/qwatson

QWatson is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>
"""

import os
import sys


version_info = (0, 4, 0, 'dev0')
__version__ = '.'.join(map(str, version_info))
__appname__ = 'QWatson'
__namever__ = __appname__ + " " + __version__
__date__ = '16/01/2019'
__project_url__ = "https://github.com/jnsebgosselin/qwatson"
__releases_url__ = __project_url__ + "/releases"
__releases_api__ = ("https://api.github.com/repos/jnsebgosselin/qwatson/"
                    "releases")


def is_frozen():
    """
    Return whether the application is running from a frozen exe or if it
    is running from the Python source files.

    See: https://stackoverflow.com/a/42615559/4481445
    """
    return getattr(sys, 'frozen', False)


if is_frozen():
    __rootdir__ = sys._MEIPASS
else:
    __rootdir__ = os.path.dirname(os.path.realpath(__file__))
