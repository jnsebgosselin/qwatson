![QWatson - A simple Qt-GUI for the Watson time-tracker](
./qwatson/ressources/qwatson_banner.png)

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](./LICENSE)
[![Build status](https://ci.appveyor.com/api/projects/status/f6hdeg9fyp1huxab?svg=true)](https://ci.appveyor.com/project/jnsebgosselin/qwatson)
[![codecov](https://codecov.io/gh/jnsebgosselin/qwatson/branch/master/graph/badge.svg)](https://codecov.io/gh/jnsebgosselin/qwatson)

QWatson is a simple GUI entirely written in Python with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) for the [Watson CLI time tracker](http://tailordev.github.io/Watson/) developed by [TailorDev](https://tailordev.fr). It is inspired by the time tracker developed by [Project Hamster](https://github.com/projecthamster/) that I love and used for several years when I was working in Linux. Unfortunately, I was not able to find any open source equivalent for the Windows platform and decided to write my own when I learned about the existence of Watson.

Many thanks to [TailorDev](https://tailordev.fr) for sharing their awesome work.

![screenshot](https://github.com/jnsebgosselin/qwatson/blob/master/images/qwatson_printscreen.png)

## To Know More About Watson

https://tailordev.fr/blog/2016/02/05/a-day-tracking-my-time-with-watson/<br>
https://tailordev.fr/blog/2016/03/31/watson-community-tools/<br>
https://tailordev.fr/blog/2017/06/07/le-lab-5-crick-a-backend-for-watson-time-tracker/

## Installation

QWatson is still in an early stage of development, so use at your own risk! A, installer and a binary for the Windows platform are available for download [here](https://github.com/jnsebgosselin/qwatson/releases/latest) or you can run it directly from source by cloning the repository and installing the required dependencies ([arrow](https://arrow.readthedocs.io/en/latest/), [click](http://click.pocoo.org/5/), [requests](http://docs.python-requests.org/en/master/), and [pyqt5](https://www.riverbankcomputing.com/software/pyqt/intro)).

## License

QWatson is released under the GPLv3 License. See the bundled LICENSE file for details.
