import os

from nova.core import NovaError
from nova.core.deploy.deploy_stack import DeployStack
from tests.cli.utils import NovaTestCase, TestManagerProvider

try:
    import mock
except ImportError:
    import unittest.mock as mock


class NovaDeployTestCase(NovaTestCase):

    def test_e2e_existing_revision_success(self):
        nova_descriptor_file = '%s/nova.yml' % os.path.dirname(os.path.realpath(__file__))
        manager_provider = TestManagerProvider()
        DeployStack(
            environment_name='test-environment',
            stack_name='test-stack',
            aws_profile=None,
            manager_provider=manager_provider,
            nova_descriptor_file=nova_descriptor_file
        ).deploy()

        manager_provider.mock_aws_manager.s3_head.assert_called_with('my-bucket', 'test-service/0.0.1.tar.gz')
        manager_provider.mock_aws_manager.create_deployment.assert_called_with(
            'some-deploy-id',
            'some-deployment-group',
            mock.ANY,
            'my-bucket',
            'test-service/0.0.1.tar.gz'
        )

    def test_deploy_without_app_id_set(self):
        try:
            nova_descriptor_file = '%s/nova_no_app_id.yml' % os.path.dirname(os.path.realpath(__file__))
            manager_provider = TestManagerProvider()
            DeployStack(
                environment_name='test-environment',
                stack_name='test-stack',
                aws_profile=None,
                manager_provider=manager_provider,
                nova_descriptor_file=nova_descriptor_file
            ).deploy()
        except NovaError as e:
            self.assertEqual(e.message, "Environment 'test-environment' does not have 'deployment_application_id' set!")
        else:
            self.fail('NovaError not raised')
