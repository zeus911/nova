import os

from nova.cli.controllers.deploy.deploy import INCORRECT_ARGS_USAGE
from nova.cli.main import get_test_app
from nova.core import NovaError
from tests.cli.utils import NovaTestCase, TestManagerProvider

try:
    import mock
except ImportError:
    import unittest.mock as mock


class NovaDeployTestCase(NovaTestCase):

    def setUp(self):
        self.manager_provider = TestManagerProvider()
        aws_manager_patcher = mock.patch(
            'nova.cli.controllers.deploy.deploy.ManagerProvider',
            return_value=self.manager_provider
        )
        aws_manager_patcher.start()
        self.addCleanup(aws_manager_patcher.stop)

    def test_deploy_no_args(self):
        with get_test_app(argv=['deploy']) as app:
            try:
                app.run()
            except NovaError as e:
                self.assertEqual(e.message, INCORRECT_ARGS_USAGE)

    def test_deploy(self):
        nova_descriptor_file = '%s/nova.yml' % os.path.dirname(os.path.realpath(__file__))
        with get_test_app(argv=[
            'deploy',
            'test-environment',
            'test-stack',
            '--file',
            nova_descriptor_file
        ]) as app:
            app.run()
        self.manager_provider.mock_aws_manager.create_deployment.assert_called_once_with(
            'some-deploy-id',
            'some-deployment-group',
            mock.ANY,
            'my-bucket',
            'test-service/0.0.1.tar.gz'
        )

    def test_no_deploy(self):
        nova_descriptor_file = '%s/nova.yml' % os.path.dirname(os.path.realpath(__file__))
        with get_test_app(argv=[
            'deploy',
            'test-environment',
            'test-stack',
            '--file',
            nova_descriptor_file,
            '--no-deployment'
        ]) as app:
            app.run()
        self.manager_provider.mock_aws_manager.create_deployment.assert_not_called()
