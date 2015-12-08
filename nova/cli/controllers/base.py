"""nova base controller."""

from cement.core.controller import CementBaseController, expose
import pkg_resources


VERSION = pkg_resources.require("gilt-nova")[0].version

BANNER = """
NOVA Service Tools v%s
Copyright (c) 2016 Gilt Groupe
""" % VERSION


class NovaBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = 'NOVA service tools'
        arguments = [
            (['-v', '--version'], dict(action='version', version=BANNER)),
        ]

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()
