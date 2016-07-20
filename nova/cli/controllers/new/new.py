"""nova setup controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
from nova.cli.controllers import new
from flask import Flask, render_template
from webbrowser import open_new_tab
from cement.core.controller import CementBaseController, expose


class NovaNewController(CementBaseController):
    class Meta:
        label = 'new'
        stacked_on = 'base'
        stacked_type = 'nested'
        description = 'Create a new NOVA descriptor setup'
        usage = "nova new"

    @expose(hide=True)
    def default(self):
        app = Flask('Nova', template_folder=os.path.join(new.__path__[0], 'templates'))

        @app.route("/")
        def index():
            return render_template('index.html')

        open_new_tab('http://localhost:5000')
        app.run()
