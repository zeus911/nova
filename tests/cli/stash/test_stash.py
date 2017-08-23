from nova.cli.controllers.stash.stash import INCORRECT_GET_ARGS_USAGE, INCORRECT_PUT_ARGS_USAGE
from nova.cli.main import get_test_app
from nova.core import NovaError
from tests.cli.utils import NovaTestCase


class NovaStackTestCase(NovaTestCase):

    def test_stash_get(self):
        with self.assertRaises(SystemExit) as exit_code:
            with get_test_app(argv=['stash', 'get']) as app:
                try:
                    app.run()
                except NovaError as e:
                    self.assertEqual(e.message, INCORRECT_GET_ARGS_USAGE)
            self.assertEqual(exit_code.exception.code, 0)

    def test_stash_put(self):
        with self.assertRaises(SystemExit) as exit_code:
            with get_test_app(argv=['stash', 'put']) as app:
                try:
                    app.run()
                except NovaError as e:
                    self.assertEqual(e.message, INCORRECT_PUT_ARGS_USAGE)
            self.assertEqual(exit_code.exception.code, 0)
