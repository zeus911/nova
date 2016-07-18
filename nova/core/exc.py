"""nova exception classes."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from termcolor import colored


class NovaError(Exception):
    """Generic errors."""

    def __init__(self, message):
        self.message = message
        # Call the base class constructor with the parameters it needs
        super(Exception, self).__init__(message)

    def __str__(self):
        return colored(self.message, color='red')


class NovaConfigError(NovaError):
    """Config related errors."""
    pass


class NovaRuntimeError(NovaError):
    """Generic runtime errors."""
    pass


class NovaArgumentError(NovaError):
    """Argument related errors."""
    pass
