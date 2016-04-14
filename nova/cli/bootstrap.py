"""nova bootstrapping."""

# All built-in application controllers should be imported, and registered
# in this file in the same way as NovaBaseController.
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from cement.core import handler
from nova.cli.controllers.base import NovaBaseController
from nova.cli.controllers.update.update import NovaUpdateController
from nova.cli.controllers.deploy.deploy import NovaDeploymentsController
from nova.cli.controllers.stack.stack import NovaStacksController
from nova.cli.controllers.stash.stash import NovaStashController


def load(app):
    """
    Register all application controllers with the core handler.

    :param app: The nova app
    """
    handler.register(NovaBaseController)
    handler.register(NovaUpdateController)
    handler.register(NovaDeploymentsController)
    handler.register(NovaStacksController)
    handler.register(NovaStashController)
