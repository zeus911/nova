import os

from nova.cli.controllers.stack.stack import INCORRECT_CREATE_ARGS_USAGE, INCORRECT_UPDATE_ARGS_USAGE
from nova.cli.main import get_test_app
from nova.core import NovaError
from tests.cli.utils import NovaTestCase, TestManagerProvider
from tests.core import StackResult

try:
    import mock
except ImportError:
    import unittest.mock as mock


class NovaStackTestCase(NovaTestCase):

    def setUp(self):
        self.manager_provider = TestManagerProvider()
        aws_manager_patcher = mock.patch(
            'nova.cli.controllers.stack.stack.ManagerProvider',
            return_value=self.manager_provider
        )
        aws_manager_patcher.start()
        self.addCleanup(aws_manager_patcher.stop)

    def test_stack_create_no_args(self):
        with get_test_app(argv=['stack', 'create']) as app:
            try:
                app.run()
            except NovaError as e:
                self.assertEqual(e.message, INCORRECT_CREATE_ARGS_USAGE)

    def test_stack_update_no_args(self):
        with get_test_app(argv=['stack', 'update']) as app:
            try:
                app.run()
            except NovaError as e:
                self.assertEqual(e.message, INCORRECT_UPDATE_ARGS_USAGE)

    def test_stack_create(self):
        self.manager_provider.mock_aws_manager.get_stack.return_value = StackResult("CREATE_COMPLETE")
        nova_descriptor_file = '%s/nova.yml' % os.path.dirname(os.path.realpath(__file__))
        with get_test_app(argv=[
            'stack',
            'create',
            'test-environment',
            '--file',
            nova_descriptor_file
        ]) as app:
            app.run()
        self.manager_provider.mock_aws_manager.create_stack.assert_called_with(
            'test-service',
            mock.ANY
        )

    def test_stack_update(self):
        self.manager_provider.mock_aws_manager.get_stack.return_value = StackResult("UPDATE_COMPLETE")
        nova_descriptor_file = '%s/nova.yml' % os.path.dirname(os.path.realpath(__file__))
        with get_test_app(argv=[
            'stack',
            'update',
            'test-environment',
            '--file',
            nova_descriptor_file
        ]) as app:
            app.run()
        self.manager_provider.mock_aws_manager.update_stack.assert_called_with(
            'test-service',
            mock.ANY,
            mock.ANY,
            mock.ANY
        )
