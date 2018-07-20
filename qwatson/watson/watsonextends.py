# -*- coding: utf-8 -*-

# Copyright © 2018 Jean-Sébastien Gosselin
# https://github.com/jnsebgosselin/qwatson
#
# This file is part of QWatson.
# Licensed under the terms of the GNU General Public License.

import os
import watson
from watson.watson import WatsonError, make_json_writer, safe_save, arrow
from watson.frames import uuid, namedtuple


HEADERS = ('start', 'stop', 'project', 'id', 'tags', 'updated_at', 'message')
watson.frames.HEADERS = HEADERS


class Frame(namedtuple('Frame', HEADERS)):
    """
    This an extension of the Frame class to support adding comments to Frame.
    """

    def __new__(cls, start, stop, project, id, tags=None, updated_at=None,
                message=None):
        try:
            if not isinstance(start, arrow.Arrow):
                start = arrow.get(start)

            if not isinstance(stop, arrow.Arrow):
                stop = arrow.get(stop)
        except RuntimeError as e:
            from .watson import WatsonError
            raise WatsonError("Error converting date: {}".format(e))

        start = start.to('local')
        stop = stop.to('local')

        if updated_at is None:
            updated_at = arrow.utcnow()
        elif not isinstance(updated_at, arrow.Arrow):
            updated_at = arrow.get(updated_at)

        if tags is None:
            tags = []

        return super(Frame, cls).__new__(
            cls, start, stop, project, id, tags, updated_at, message
        )

    def dump(self):
        start = self.start.to('utc').timestamp
        stop = self.stop.to('utc').timestamp
        updated_at = self.updated_at.timestamp

        return (start, stop, self.project, self.id, self.tags, updated_at,
                self.message)

    @property
    def day(self):
        return self.start.floor('day')

    def __lt__(self, other):
        return self.start < other.start

    def __lte__(self, other):
        return self.start <= other.start

    def __gt__(self, other):
        return self.start > other.start

    def __gte__(self, other):
        return self.start >= other.start


watson.frames.Frame = Frame


class Frames(watson.frames.Frames):
    """
    This an extension of the Frames class to support adding comments to Frame.
    """

    def new_frame(self, project, start, stop, tags=None, id=None,
                  updated_at=None, message=None):
        if not id:
            id = uuid.uuid4().hex
        return Frame(start, stop, project, id, tags=tags,
                     updated_at=updated_at, message=message)


watson.watson.Frames = Frames
watson.frames.Frames = Frames


class Watson(watson.watson.Watson):
    """
    This an extension of the Watson class to support adding comments to Frame.
    """

    def __init__(self, **kwargs):
        super(Watson, self).__init__(**kwargs)
        self._projects = None
        self.projects_file = os.path.join(self._dir, 'projects')

    # ---- Watson override

    def save(self):
        """
        Override of Watson save method to support adding comment to frame.
        """
        try:
            if not os.path.isdir(self._dir):
                os.makedirs(self._dir)

            if self._current is not None and self._old_state != self._current:
                if self.is_started:
                    current = {
                        'project': self.current['project'],
                        'start': self._format_date(self.current['start']),
                        'tags': self.current['tags'],
                        'message': self.current.get('message'),
                    }
                else:
                    current = {}

                safe_save(self.state_file, make_json_writer(lambda: current))
                self._old_state = current

            if self._frames is not None and self._frames.changed:
                safe_save(self.frames_file,
                          make_json_writer(self.frames.dump))

            if self._config_changed:
                safe_save(self.config_file, self.config.write)

            if self._last_sync is not None:
                safe_save(self.last_sync_file,
                          make_json_writer(self._format_date, self.last_sync))

            if self._projects is not None:
                safe_save(self.projects_file,
                          make_json_writer(lambda: self.projects))
        except OSError as e:
            raise WatsonError(
                "Impossible to write {}: {}".format(e.filename, e)
            )

    @property
    def current(self):
        if self._current is None:
            self.current = self._load_json_file(self.state_file)

        if self._old_state is None:
            self._old_state = self._current

        return dict(self._current)

    @current.setter
    def current(self, value):
        if not value or 'project' not in value:
            self._current = {}

            if self._old_state is None:
                self._old_state = {}

            return

        start = value.get('start', arrow.now())

        if not isinstance(start, arrow.Arrow):
            start = self._parse_date(start)

        self._current = {
            'project': value['project'],
            'start': start,
            'tags': value.get('tags') or [],
            'message': value.get('message'),
        }

        if self._old_state is None:
            self._old_state = self._current

    def stop(self):
        """
        Override of Watson stop method to support adding comment to frame.
        """
        if not self.is_started:
            raise WatsonError("No project started.")

        old = self.current
        frame = self.frames.add(
            old['project'], old['start'], arrow.now(), tags=old['tags'],
            message=old.get('message')
        )
        self.current = None

        return frame

    # ---- Watson extension

    @property
    def projects(self):
        """
        Get or set the list of all the existing projects. The project list
        are returned sorted by name.
        """
        if self._projects is None:
            self._projects = sorted(set(
                [''] + list(self.frames['project']) +
                self._load_json_file(self.projects_file, type=list)
                ))
        else:
            self._projects = sorted(set(
                [''] + list(self.frames['project']) + self._projects
                ))

        return self._projects

    @projects.setter
    def projects(self, projects):
        self._projects = sorted(set(projects))

    def add_project(self, project):
        if project in self.projects:
            raise ValueError('Project "%s" already exist' % project)

        self._projects = self._projects = sorted(set(
            [str(project)] + self._projects))

    def delete_project(self, project):
        """Delete the project and all related frames."""
        if project not in self.projects:
            raise ValueError('Project "%s" does not exist' % project)

        for frame in self.frames:
            if frame.project == project:
                del self.frames[frame.id]

        self.save()
