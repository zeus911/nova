from nova.cli.controllers.stash.stash import INCORRECT_GET_ARGS_USAGE, INCORRECT_PUT_ARGS_USAGE
from nova.cli.main import get_test_app
from nova.core import NovaError
from tests.cli.utils import NovaTestCase


class NovaStackTestCase(NovaTestCase):

    def test_stash_get(self):
        with get_test_app(argv=['stash', 'get']) as app:
            try:
                app.run()
            except NovaError as e:
                self.assertEqual(e.msg, INCORRECT_GET_ARGS_USAGE)

    def test_stash_put(self):
        with get_test_app(argv=['stash', 'put']) as app:
            try:
                app.run()
            except NovaError as e:
                self.assertEqual(e.msg, INCORRECT_PUT_ARGS_USAGE)
