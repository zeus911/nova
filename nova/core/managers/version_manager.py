from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import subprocess


class VersionManager(object):

    def __init__(self):
        self._current_version = None

    def current_version(self, forced_version=None):
        if self._current_version is None:
            if forced_version is None:
                git_version = subprocess.check_output(['git', 'describe', '--tags', '--dirty', '--always'])
                console_encoding = sys.stdout.encoding or 'utf-8'
                self._current_version = git_version.decode(console_encoding).strip('v').strip()
            else:
                self._current_version = forced_version
        return self._current_version
