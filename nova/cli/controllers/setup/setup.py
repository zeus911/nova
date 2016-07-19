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
        nova_install_dir = '/opt/nova'

        print("installing NOVA instance scripts, please wait...")
        instance_scripts_path = os.path.join(templates.__path__[0], 'instance-scripts')

        if not os.path.exists(nova_install_dir):
            os.makedirs(nova_install_dir)

        for f in os.listdir(instance_scripts_path):
            file_name = os.path.join(instance_scripts_path, f)
            shutil.copy(file_name, nova_install_dir)

        # This is a workaround so our tests don't see this as actual Nova Python source...
        os.rename(
            os.path.join(instance_scripts_path, 'configure-cloudwatch-logs-agent.py.txt'),
            os.path.join(instance_scripts_path, 'configure-cloudwatch-logs-agent.py')
        )
