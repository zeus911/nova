from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import sys
import subprocess
import pkg_resources
from six.moves import input
import six.moves.xmlrpc_client
from termcolor import colored
from nova.core.exc import NovaError


def check_latest_version():
    try:
        current = pkg_resources.require("gilt-nova")[0].version
        pypi = six.moves.xmlrpc_client.ServerProxy('http://pypi.python.org/pypi')
        available = pypi.package_releases('gilt-nova')
        major_available = available[0].split('.')[0]
        major_current = current.split('.')[0]
        if available[0] != current:
            print(colored("The latest version of nova is '%s', please upgrade!" % available[0], color='yellow'))

        if major_available != major_current:
            raise NovaError('There has been a breaking change, please upgrade before continuing!')
    except Exception:
        pass


def get_git_revision():
    git_version = subprocess.check_output(['git', 'describe', '--tags', '--dirty', '--always'])
    return git_version.decode(sys.stdout.encoding).strip('v').strip()


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    :param question: is a string that is presented to the user.
    :param default: is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()

        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write(colored("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n", color='cyan'))
