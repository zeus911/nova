from nova.cli.controllers.stack.stack import INCORRECT_CREATE_ARGS_USAGE, INCORRECT_UPDATE_ARGS_USAGE
from nova.cli.main import get_test_app
from nova.core import NovaError
from tests.cli.utils import NovaTestCase


class NovaStackTestCase(NovaTestCase):

    def test_stack_create(self):
        with get_test_app(argv=['stack', 'create']) as app:
            try:
                app.run()
            except NovaError as e:
                self.assertEqual(e.msg, INCORRECT_CREATE_ARGS_USAGE)

    def test_stack_update(self):
        with get_test_app(argv=['stack', 'update']) as app:
            try:
                app.run()
            except NovaError as e:
                self.assertEqual(e.msg, INCORRECT_UPDATE_ARGS_USAGE)