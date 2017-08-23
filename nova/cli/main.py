"""
nova main application entry point.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
import traceback

from cement.core.foundation import CementApp
from cement.utils.misc import init_defaults
from cement.core.exc import FrameworkError, CaughtSignal
from cement.ext.ext_argparse import ArgParseArgumentHandler
from nova.core import exc

# this has to happen after you import sys, but before you import anything
# from Cement "source: https://github.com/datafolklabs/cement/issues/290"
if '--debug' in sys.argv:
    sys.argv.remove('--debug')
    TOGGLE_DEBUG = True
else:
    TOGGLE_DEBUG = False


# Application default.  Should update config/nova.conf to reflect any
# changes, or additions here.
defaults = init_defaults('nova')

# All internal/external plugin configurations are loaded from here
defaults['nova']['plugin_config_dir'] = '~/.nova/plugins.d'
# External plugins (generally, do not ship with application code)
defaults['nova']['plugin_dir'] = '~/.nova/plugins'
# External templates (generally, do not ship with application code)
defaults['nova']['template_dir'] = '~/.nova/templates'


class NovaArgHandler(ArgParseArgumentHandler):
    class Meta:
        label = 'nova_args_handler'

    def error(self, message):
        super(NovaArgHandler, self).error("unknown args")


class NovaApp(CementApp):
    class Meta:
        label = 'nova'
        config_defaults = defaults
        extensions = ['argcomplete']

        # All built-in application bootstrapping (always run)
        bootstrap = 'nova.cli.bootstrap'

        # Optional plugin bootstrapping (only run if plugin is enabled)
        plugin_bootstrap = 'nova.cli.plugins'

        # Internal templates (ship with application code)
        template_module = 'nova.core.templates'

        arg_handler = NovaArgHandler

        debug = TOGGLE_DEBUG
        exit_on_close = True


# Define the application object outside of main, as some libraries might wish
# to import it as a global (rather than passing it into another class/func)

app = NovaApp()


def handle_exception(error):
    if type(error) is exc.NovaError:
        # Catch our application errors and exit 1 (error)
        print('NovaError > %s' % error)
        return 1
    if type(error) is CaughtSignal:
        # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
        print('CaughtSignal > %s' % error)
        return 0
    if type(error) is FrameworkError:
        # Catch framework errors and exit 1 (error)
        print('FrameworkError > %s' % error)
        return 2
    print('Unexpected Error > %s' % error)
    return 2


# noinspection PyBroadException
def main():
    with app:
        # Default our exit status to 0 (non-error)
        exit_code = 0
        try:
            global sys

            # Dump all arguments into nova log
            app.log.debug(sys.argv)

            app.run()
        except Exception as e:
            exit_code = handle_exception(e)
        finally:
            # Print an exception (if it occurred) and --debug was passed
            if app.debug:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_traceback is not None:
                    traceback.print_exc()

        # Close the application
        app.close(exit_code)


def get_test_app(**kw):
    return NovaApp(**kw)

if __name__ == '__main__':
    main()
