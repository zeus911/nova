"""nova base controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from cement.core.controller import CementBaseController, expose
from nova.core import check_latest_version
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
        check_latest_version()
        self.app.args.print_help()
