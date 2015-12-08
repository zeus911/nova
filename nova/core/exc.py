"""nova exception classes."""
from termcolor import colored


class NovaError(Exception):
    """Generic errors."""
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return colored(self.msg, color='red')


class NovaConfigError(NovaError):
    """Config related errors."""
    pass


class NovaRuntimeError(NovaError):
    """Generic runtime errors."""
    pass


class NovaArgumentError(NovaError):
    """Argument related errors."""
    pass
