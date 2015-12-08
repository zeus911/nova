"""nova bootstrapping."""

# All built-in application controllers should be imported, and registered
# in this file in the same way as NovaBaseController.

from cement.core import handler
from nova.cli.controllers.base import NovaBaseController
from nova.cli.controllers.update.update import NovaUpdateController
from nova.cli.controllers.deploy.deploy import NovaDeploymentsController
from nova.cli.controllers.stack.stack import NovaStacksController


def load(app):
    handler.register(NovaBaseController)
    handler.register(NovaUpdateController)
    handler.register(NovaDeploymentsController)
    handler.register(NovaStacksController)
