"""nova stacks controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from cement.core.controller import CementBaseController, expose
from nova.core.exc import NovaError
from nova.core.stack.create_stack import CreateStack
from nova.core.stack.update_stack import UpdateStack


class NovaStacksController(CementBaseController):
    class Meta:
        label = 'stack'
        description = 'NOVA service stack tools'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['-p', '--profile'], dict(help='Override nova.yml AWS profile')),
            (['environment'], dict(action='store', nargs='*'))
        ]
        usage = "nova stack [create|update] <environment>"

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()

    @expose(help='Create NOVA service stack')
    def create(self):
        if self.app.pargs.environment:
            profile = self.app.pargs.profile
            CreateStack(profile, self.app.pargs.environment[0])
        else:
            raise NovaError("You must provide an environment to create")

    @expose(help='Update NOVA service stack')
    def update(self):
        if self.app.pargs.environment:
            profile = self.app.pargs.profile
            UpdateStack(profile, self.app.pargs.environment[0])
        else:
            raise NovaError("You must provide an environment to update")
