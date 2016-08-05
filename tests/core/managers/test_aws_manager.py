from contextlib import contextmanager
import shutil
import tempfile
from botocore.exceptions import ClientError

from nova.core.managers.aws_manager import AwsManager
from nova.core.spec.environment import Environment
from nova.core.spec.service import Service
from nova.core.spec.stack import Stack
from tests.cli.utils import NovaTestCase

try:
    import mock
except ImportError:
    import unittest.mock as mock


@mock.patch('boto3.session.Session')
class NovaAwsManagerTestCase(NovaTestCase):

    def test_account_alias(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        mock_session.return_value.client.return_value.list_account_aliases.return_value = {'AccountAliases': ['test-account']}
        self.assertEqual(aws_manager.account_alias, 'test-account')

    def test_create_bucket_exists(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        aws_manager.create_bucket('some-test-bucket', '')
        mock_session.return_value.client.return_value.head_bucket.assert_called_with(Bucket='some-test-bucket')
        mock_session.return_value.client.return_value.create_bucket.assert_not_called()

    def test_create_bucket(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        mock_session.return_value.client.return_value.head_bucket.side_effect = ClientError({'Error': {}}, 'test-op')
        aws_manager.create_bucket('some-test-bucket', '')
        mock_session.return_value.client.return_value.head_bucket.assert_called_with(Bucket='some-test-bucket')
        mock_session.return_value.client.return_value.create_bucket.assert_called_with(Bucket='some-test-bucket')

    def test_s3_put(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        aws_manager.s3_put('some-test-bucket', 'body', 'key', 'meta')
        mock_session.return_value.client.return_value.put_object.assert_called_with(
            Bucket='some-test-bucket',
            Body='body',
            Key='key',
            Metadata='meta'
        )

    def test_s3_get(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        mock_session.return_value.client.return_value.get_object.side_effect = ClientError({'Error': {}}, 'test-op')
        response = aws_manager.s3_get('some-test-bucket', 'key')
        mock_session.return_value.client.return_value.get_object.assert_called_with(Bucket='some-test-bucket', Key='key')
        self.assertEqual(response, None)

    def test_s3_get_exists(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        mock_session.return_value.client.return_value.get_object.return_value = 'response'
        response = aws_manager.s3_get('some-test-bucket', 'key')
        mock_session.return_value.client.return_value.get_object.assert_called_with(Bucket='some-test-bucket', Key='key')
        self.assertEqual(response, 'response')

    def test_s3_head(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        mock_session.return_value.client.return_value.get_object.side_effect = ClientError({'Error': {}}, 'test-op')
        response = aws_manager.s3_get('some-test-bucket', 'key')
        mock_session.return_value.client.return_value.get_object.assert_called_with(Bucket='some-test-bucket', Key='key')
        self.assertEqual(response, None)

    def test_s3_head_exists(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        mock_session.return_value.client.return_value.head_object.return_value = 'response'
        response = aws_manager.s3_head('some-test-bucket', 'key')
        mock_session.return_value.client.return_value.head_object.assert_called_with(Bucket='some-test-bucket', Key='key')
        self.assertEqual(response, 'response')

    def test_create_stack(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        mock_session.return_value.resource.return_value.create_stack.return_value = '123456'
        stack_id = aws_manager.create_stack('my-service', 'template')
        self.assertEqual(stack_id, '123456')

    @mock.patch('nova.core.managers.aws_manager.query_yes_no')
    def test_create_stack(self, mock_user_query, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')

        mock_user_query.return_value = 'y'
        mock_session.return_value.client.return_value.create_change_set.return_value = {'Id': '123456789'}
        mock_session.return_value.client.return_value.describe_change_set.return_value = {}

        cf_stack = mock.MagicMock(stack_name='my-service-prod')
        aws_manager.update_stack('my-service', 'template', 'changeset_id', cf_stack)

        mock_session.return_value.client.return_value.create_change_set.assert_called_with(
            StackName='my-service-prod',
            TemplateBody='template',
            Capabilities=["CAPABILITY_IAM"],
            ChangeSetName='changeset_id'
        )

        mock_session.return_value.client.return_value.execute_change_set.assert_called_with(
            ChangeSetName='changeset_id',
            StackName='my-service-prod'
        )

    @mock.patch('os.path')
    @mock.patch('git.Repo')
    def test_create_and_upload_stack_template(self, mock_git_repo, mock_os_path, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')
        stack = Stack('my-stack', 'prod', 'template.json', None, None, 'OneAtATime',  None, None, None, None, None, None)
        environment = Environment('my-env', 'test-profile', 'us-east-1', None, 'my-deploy-arn', 'my-deploy-bucket', None, [stack])
        service = Service('my-service', 'my-team', 9000, '/health', None, [environment])

        mock_os_path.return_value.exists.return_value = True
        mock_git_repo.return_value.is_dirty.return_value = False
        mock_git_repo.return_value.git.return_value.rev_list.return_value = False
        mock_session.return_value.client.return_value.head_object.return_value = 'response'
        m = mock.mock_open(read_data='test template'.encode('utf-8'))

        with mock.patch('nova.core.managers.aws_manager.open', m, create=True):
            aws_manager.create_and_upload_stack_template('my-bucket', service, environment)

        mock_session.return_value.client.return_value.head_object.assert_called_with(
            Bucket='my-bucket',
            Key='my-service/my-stack_template.json',
            IfMatch='5a6bce91d3a7b4667d36c1509bb0efc4'
        )

    def test_push_revision(self, mock_session):
        aws_manager = AwsManager('test-profile', 'us-east-1')

        mock_session.return_value.client.return_value.head_object.return_value = {'ETag': '1'}

        with self._temporary_directory() as nova_dir:
            aws_manager.push_revision('my-deployment-bucket', '0.0.1', 'code-deploy-app', nova_dir)

        mock_session.return_value.client.return_value.register_application_revision.assert_called_with(
            applicationName='code-deploy-app',
            revision={
                'revisionType': 'S3',
                's3Location': {
                    'bucket': 'my-deployment-bucket',
                    'key': '0.0.1',
                    'bundleType': 'tgz',
                    'eTag': '1'
                }
            }
        )

    @staticmethod
    @contextmanager
    def _temporary_directory():
        name = tempfile.mkdtemp(prefix='nova-test')
        try:
            yield name
        finally:
            shutil.rmtree(name)