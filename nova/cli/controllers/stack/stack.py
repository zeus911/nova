"""nova stacks controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from cement.core.controller import CementBaseController, expose
from nova.core.exc import NovaError
from nova.core.managers.manager_provider import ManagerProvider
from nova.core.stack.create_stack import CreateStack
from nova.core.stack.update_stack import UpdateStack

INCORRECT_CREATE_ARGS_USAGE = "You must provide an environment to create"

INCORRECT_UPDATE_ARGS_USAGE = "You must provide an environment to update"


class NovaStacksController(CementBaseController):
    class Meta:
        label = 'stack'
        description = 'NOVA service stack tools'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['-f', '--file'], dict(help='Specify the nova service descriptor file to use.')),
            (['-p', '--profile'], dict(help='Override nova.yml AWS profile')),
            (['-o', '--output'], dict(help='Specify a file to output the template to.')),
            (['--no-docker-args'], dict(
                help='Do not populate DockerDeployment* CF variables.',
                dest='include_docker',
                action='store_false',
                default=True
            )),
            (['environment'], dict(action='store', nargs='*'))
        ]
        usage = "nova stack [create|update] <environment>"

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()

    @expose(help='Create NOVA service stack')
    def create(self):
        cf_template_out = self.app.pargs.output
        nova_descriptor_file = self.app.pargs.file
        include_docker = self.app.pargs.include_docker
        if self.app.pargs.environment:
            profile = self.app.pargs.profile
            CreateStack(
                aws_profile=profile,
                environment_name=self.app.pargs.environment[0],
                manager_provider=ManagerProvider(),
                cf_template_out=cf_template_out,
                nova_descriptor_file=nova_descriptor_file,
                include_docker=include_docker
            ).create()
        else:
            raise NovaError(INCORRECT_CREATE_ARGS_USAGE)

    @expose(help='Update NOVA service stack')
    def update(self):
        cf_template_out = self.app.pargs.output
        nova_descriptor_file = self.app.pargs.file
        include_docker = self.app.pargs.include_docker
        if self.app.pargs.environment:
            profile = self.app.pargs.profile
            UpdateStack(
                aws_profile=profile,
                environment_name=self.app.pargs.environment[0],
                manager_provider=ManagerProvider(),
                cf_template_out=cf_template_out,
                nova_descriptor_file=nova_descriptor_file,
                include_docker=include_docker
            ).update()
        else:
            raise NovaError(INCORRECT_UPDATE_ARGS_USAGE)
