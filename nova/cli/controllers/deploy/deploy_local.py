"""nova local deployments controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from cement.core.controller import CementBaseController, expose

from nova.core.deploy.deploy_local_stack import DeployLocalStack
from nova.core.exc import NovaError


class NovaLocalDeploymentsController(CementBaseController):
    class Meta:
        label = 'deploy-local'
        description = 'NOVA service local deployment tools'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['-p', '--profile'], dict(help='Override nova.yml AWS profile.')),
            (['-O', '--output'], dict(help='Output the revision archive to a given directory.')),
            (['-ip'], dict(help='The IP address of the instance to deploy to.', required=True)),
            (['deploy_args'], dict(action='store', nargs='*'))
        ]

    @expose(hide=True, help='Deploy a NOVA service stack locally')
    def default(self):
        profile = self.app.pargs.profile
        output_dir = self.app.pargs.output
        ip = self.app.pargs.ip
        deploy_args = self.app.pargs.deploy_args
        if len(deploy_args) == 2:
            DeployLocalStack(profile, output_dir, ip, deploy_args[0], deploy_args[1])
        elif len(deploy_args) == 3:
            DeployLocalStack(profile, output_dir, ip, deploy_args[0], deploy_args[1], deploy_args[2])
        else:
            raise NovaError("Usage: deploy-local [options ...] <environment> <stack> [version]")
