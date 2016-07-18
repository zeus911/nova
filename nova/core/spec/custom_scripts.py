from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


class CustomScripts(object):

    def __init__(self,
                 app_stop_scripts=list(),
                 before_install_scripts=list(),
                 after_install_scripts=list(),
                 app_start_scripts=list(),
                 validate_scripts=list()):
        self.app_stop_scripts = app_stop_scripts
        self.before_install_scripts = before_install_scripts
        self.after_install_scripts = after_install_scripts
        self.app_start_scripts = app_start_scripts
        self.validate_scripts = validate_scripts

    @property
    def app_stop_scripts_for_app_spec(self):
        return [{'location': s} for s in self.app_stop_scripts]

    @property
    def before_install_scripts_for_app_spec(self):
        return [{'location': s} for s in self.before_install_scripts]

    @property
    def after_install_scripts_for_app_spec(self):
        return [{'location': s} for s in self.after_install_scripts]

    @property
    def app_start_scripts_for_app_spec(self):
        return [{'location': s} for s in self.app_start_scripts]

    @property
    def validate_scripts_for_app_spec(self):
        return [{'location': s} for s in self.validate_scripts]
