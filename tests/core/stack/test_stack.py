import os
import json
from nova.core.stack.create_stack import CreateStack
from nova.core.stack.update_stack import UpdateStack
from tests.cli.utils import NovaTestCase, TestManagerProvider

try:
    import mock
except ImportError:
    import unittest.mock as mock


class NovaStackTestCase(NovaTestCase):

    def test_stack_create(self):
        nova_descriptor_file = '%s/nova_create.yml' % os.path.dirname(os.path.realpath(__file__))
        expected_template_out = '%s/expected_create_stack.json' % os.path.dirname(os.path.realpath(__file__))
        with open(expected_template_out, 'r') as expected_template_out_file:
            expected_template = json.loads(expected_template_out_file.read())

        manager_provider = TestManagerProvider()
        manager_provider.mock_aws_manager.get_stack = mock.MagicMock(return_value=StackResult("CREATE_COMPLETE"))

        create_stack = CreateStack(
            'my-profile',
            'test-environment',
            manager_provider,
            nova_descriptor_file=nova_descriptor_file
        )
        create_stack.create()

        actual_template = json.loads(create_stack.cloudformation_template)
        #self.assertDictContainsSubset(actual_template, expected_template)

    def test_stack_update(self):
        nova_descriptor_file = '%s/nova_update.yml' % os.path.dirname(os.path.realpath(__file__))
        expected_template_out = '%s/expected_update_stack.json' % os.path.dirname(os.path.realpath(__file__))
        with open(expected_template_out, 'r') as expected_template_out_file:
            expected_template = json.loads(expected_template_out_file.read())

        manager_provider = TestManagerProvider()
        manager_provider.mock_aws_manager.get_stack = mock.MagicMock(return_value=StackResult("UPDATE_COMPLETE"))

        update_stack = UpdateStack(
            'my-profile',
            'test-environment',
            manager_provider,
            nova_descriptor_file=nova_descriptor_file
        )
        update_stack.update()

        actual_cf_template = json.loads(update_stack.cloudformation_template)
        #self.assertDictContainsSubset(actual_cf_template, expected_template)


class StackResult(object):
    def __init__(self, status):
        self.stack_status = status
        self.outputs = None
