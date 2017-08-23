import os

from nova.cli.controllers.stack.stack import INCORRECT_UPDATE_ARGS_USAGE
from nova.cli.main import get_test_app, handle_exception
from nova.core import NovaError
from tests.cli.utils import NovaTestCase, TestManagerProvider
from tests.core import StackResult

try:
    import mock
except ImportError:
    import unittest.mock as mock


class NovaExceptionHandling(NovaTestCase):
    def setUp(self):
        self.manager_provider = TestManagerProvider()
        aws_manager_patcher = mock.patch(
            'nova.cli.controllers.stack.stack.ManagerProvider',
            return_value=self.manager_provider
        )
        aws_manager_patcher.start()
        self.addCleanup(aws_manager_patcher.stop)

    def test_exit_code_with_error(self):
        with self.assertRaises(SystemExit) as exit_code:
            with get_test_app(argv=['stack', 'update']) as app:
                code = 0
                try:
                    app.run()
                except NovaError as e:
                    self.assertEqual(e.message, INCORRECT_UPDATE_ARGS_USAGE)
                    code = handle_exception(e)
                finally:
                    app.close(code)
            self.assertEqual(exit_code.exception.code, 1)

    def test_exit_code_without_error(self):
        self.manager_provider.mock_aws_manager.get_stack.return_value = StackResult("CREATE_COMPLETE")
        nova_descriptor_file = '%s/nova.yml' % os.path.dirname(os.path.realpath(__file__))
        with self.assertRaises(SystemExit) as exit_code:
            with get_test_app(argv=[
                'stack',
                'create',
                'test-environment',
                '--file',
                nova_descriptor_file
            ]) as app:
                code = 0
                try:
                    app.run()
                    self.manager_provider.mock_aws_manager.create_stack.assert_called_with(
                        'test-service',
                        mock.ANY
                    )
                except Exception as e:
                    code = handle_exception(e)
                finally:
                    app.close(code)
            self.assertEqual(exit_code.exception.code, 0)

