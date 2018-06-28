![QWatson - A simple Qt-GUI for the Watson time-tracker](
./qwatson/ressources/qwatson_banner.png)

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](./LICENSE)
[![Latest release](https://img.shields.io/github/release/jnsebgosselin/qwatson.svg)](https://github.com/jnsebgosselin/qwatson/releases)
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

An installer and a binary for the Windows platform are available for download [here](https://github.com/jnsebgosselin/qwatson/releases/latest) or you can run it directly from source by cloning the repository and installing the required dependencies ([arrow](https://arrow.readthedocs.io/en/latest/), [click](http://click.pocoo.org/5/), [requests](http://docs.python-requests.org/en/master/), and [pyqt5](https://www.riverbankcomputing.com/software/pyqt/intro)).

**Important:**<br>
In order to support the addition of log messages/comments to the activity frames, QWatson is distributed with a forked version of Watson (see [Pull Request #1](https://github.com/jnsebgosselin/qwatson/pull/1)). This means that until this feature is officially supported in Watson, frames edited with QWatson won't be readable nor editable with the Watson CLI (see [Issue #37](https://github.com/jnsebgosselin/qwatson/issues/37)).

For this reason, the default path for the QWatson application folder is set differently from that of Watson, so that one does not unkowingly make its whole activity database incompatible with the Watson CLI while trying out QWatson. Therefore, if you want to read and edit activity frames previously created with the Watson CLI, you have to copy manually the file `frames` from the Watson application folder to that of QWatson. Depending on your system, the default path for the application folders might be:

- Windows: C:/Users/\<user\>/AppData/Roaming/
- MacOSX: ~/Library/Application Support/
- Linux: ~/.config/

## License

QWatson is released under the GPLv3 License. See the bundled LICENSE file for details.
