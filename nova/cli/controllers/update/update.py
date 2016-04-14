"""nova stacks controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from cement.core.controller import CementBaseController, expose
import pip


class NovaUpdateController(CementBaseController):
    class Meta:
        label = 'update'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'Update NOVA to latest version'
        usage = "nova update"

    @expose(hide=True)
    def default(self):
        print("updating NOVA, please wait...")
        # TODO Update this once open-sourced to PyPi
        pip.main(['install', '--upgrade', 'gilt-nova'])
