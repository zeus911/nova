"""nova deployments controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from cement.core.controller import CementBaseController, expose
from nova.core.deploy.deploy_stack import DeployStack
from nova.core.exc import NovaError
from nova.core.managers.manager_provider import ManagerProvider

INCORRECT_ARGS_USAGE = "Usage: deploy <environment> <stack> (<version>)"


class NovaDeploymentsController(CementBaseController):
    class Meta:
        label = 'deploy'
        description = 'NOVA service deployment tools'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['-f', '--file'], dict(help='Specify the nova service descriptor file to use.')),
            (['-p', '--profile'], dict(help='Override nova.yml AWS profile')),
            (['-n', '--no-deployment'], dict(
                help='Upload to S3 only, do not trigger code-deploy',
                dest='no_deploy',
                action='store_true',
                default=False
            )),
            (['deploy_args'], dict(action='store', nargs='*'))
        ]
        usage = "nova deploy <environment> <stack> (<version>)"

    @expose(hide=True, help='Deploy a NOVA service stack')
    def default(self):
        profile = self.app.pargs.profile
        deploy_args = self.app.pargs.deploy_args
        nova_descriptor_file = self.app.pargs.file
        manager_provider = ManagerProvider()
        deploy = not self.app.pargs.no_deploy
        if len(deploy_args) == 2:
            deployer = DeployStack(
                deploy_args[0],
                deploy_args[1],
                profile,
                manager_provider,
                deploy=deploy,
                nova_descriptor_file=nova_descriptor_file
            )
        elif len(deploy_args) == 3:
            deployer = DeployStack(
                deploy_args[0],
                deploy_args[1],
                profile,
                manager_provider,
                version=deploy_args[2],
                deploy=deploy,
                nova_descriptor_file=nova_descriptor_file
            )
        else:
            raise NovaError(INCORRECT_ARGS_USAGE)

        deployer.deploy()
