"""nova stacks controller."""

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
