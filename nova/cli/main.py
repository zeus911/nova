"""nova main application entry point."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

# this has to happen after you import sys, but before you import anything
# from Cement "source: https://github.com/datafolklabs/cement/issues/290"
if '--debug' in sys.argv:
    sys.argv.remove('--debug')
    TOGGLE_DEBUG = True
else:
    TOGGLE_DEBUG = False

from cement.core.foundation import CementApp
from cement.utils.misc import init_defaults
from cement.core.exc import FrameworkError, CaughtSignal
from nova.core import exc

# Application default.  Should update config/nova.conf to reflect any
# changes, or additions here.
defaults = init_defaults('nova')

# All internal/external plugin configurations are loaded from here
defaults['nova']['plugin_config_dir'] = '~/.nova/plugins.d'
# External plugins (generally, do not ship with application code)
defaults['nova']['plugin_dir'] = '~/.nova/plugins'
# External templates (generally, do not ship with application code)
defaults['nova']['template_dir'] = '~/.nova/templates'


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

        debug = TOGGLE_DEBUG


# Define the application object outside of main, as some libraries might wish
# to import it as a global (rather than passing it into another class/func)
app = NovaApp()


def main():
    with app:
        try:
            global sys
            # Default our exit status to 0 (non-error)
            code = 0

            # Setup the application
            #app.setup()

            # Dump all arguments into nova log
            app.log.debug(sys.argv)

            app.run()
        except exc.NovaError as e:
            # Catch our application errors and exit 1 (error)
            print('NovaError > %s' % e)
            code = 1

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('CaughtSignal > %s' % e)
            code = 0

        except FrameworkError as e:
            # Catch framework errors and exit 1 (error)
            print('FrameworkError > %s' % e)
            code = 1
        finally:
            # Print an exception (if it occurred) and --debug was passed
            if app.debug:
                import sys
                import traceback

                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_traceback is not None:
                    traceback.print_exc()

        # # Close the application
        app.close(code)


if __name__ == '__main__':
    main()
