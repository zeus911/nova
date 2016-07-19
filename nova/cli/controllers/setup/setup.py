"""nova setup controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import shutil
from cement.core.controller import CementBaseController, expose

from nova.core import templates


class NovaSetupController(CementBaseController):
    class Meta:
        label = 'setup'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'Setup NOVA scripts on a deployment host'
        usage = "nova setup"

    @expose(hide=True)
    def default(self):
        print("installing NOVA instance scripts, please wait...")
        instance_scripts_path = os.path.join(templates.__path__[0], 'instance-scripts')
        for f in os.listdir(instance_scripts_path):
            file_name = os.path.join(instance_scripts_path, f)
            shutil.copy(file_name, '/opt/nova/')
