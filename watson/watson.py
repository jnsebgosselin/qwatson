# -*- coding: utf-8 -*-

import watson
import arrow


class Watson(watson.watson.Watson):
    """A subclass of the stock Watson class with added functionalities."""

    def __init__(self, **kwargs):
        super(Watson, self). __init__(**kwargs)

    def delete_project(self, project):
        """Delete the project and all related frames."""
        if project not in self.projects:
            raise ValueError('Project "%s" does not exist' % project)

        for frame in self.frames:
            if frame.project == project:
                del self.frames[frame.id]

        self.save()
