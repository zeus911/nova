"""nova deployments controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from cement.core.controller import CementBaseController, expose
from nova.core.deploy.deploy_stack import DeployStack
from nova.core.exc import NovaError


class NovaDeploymentsController(CementBaseController):
    class Meta:
        label = 'deploy'
        description = 'NOVA service deployment tools'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['-f', '--file'], dict(help='Specify the nova service descriptor file to use.')),
            (['-p', '--profile'], dict(help='Override nova.yml AWS profile')),
            (['deploy_args'], dict(action='store', nargs='*'))
        ]
        usage = "nova deploy <environment> <stack> (<version>)"

    @expose(hide=True, help='Deploy a NOVA service stack')
    def default(self):
        profile = self.app.pargs.profile
        deploy_args = self.app.pargs.deploy_args
        nova_descriptor_file = self.app.pargs.file
        if len(deploy_args) == 2:
            DeployStack(profile, deploy_args[0], deploy_args[1], nova_descriptor_file = nova_descriptor_file)
        elif len(deploy_args) == 3:
            DeployStack(profile, deploy_args[0], deploy_args[1], version=deploy_args[2], nova_descriptor_file = nova_descriptor_file)
        else:
            raise NovaError("Usage: deploy <environment> <stack> (<version>)")
