import sys
import xmlrpclib
import pkg_resources
from termcolor import colored
from nova.core.exc import NovaError


def check_latest_version():
    current = pkg_resources.require("gilt-nova")[0].version
    pypi = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    available = pypi.package_releases('gilt-nova')
    major_available = available[0].split('.')[0]
    major_current = current.split('.')[0]
    if available[0] != current:
        print(colored("The latest version of nova is '%s', please upgrade!" % available[0], color='yellow'))

    if major_available != major_current:
        raise NovaError('There has been a breaking change, please upgrade before continuing!')


def get_git_revision():
    import subprocess
    return subprocess.check_output(['git', 'describe', '--tags', '--dirty', '--always']).strip('v').strip()


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
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write(colored("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n", color='cyan'))
