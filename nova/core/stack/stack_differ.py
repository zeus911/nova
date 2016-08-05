from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import re
import codecs
from json_delta import _udiff
from botocore.exceptions import ClientError, WaiterError
from nova.core import NovaError


class StackDiffer(object):

    def __init__(self, profile, region, manager_provider):
        self._aws_manager = manager_provider.aws_manager(profile, region)

    def diff(self, service, environment, s3_bucket):
        try:
            stack_name = self._aws_manager.get_stack(service.name).stack_name
            old_template = self._aws_manager.cloudformation_client.get_template(StackName=stack_name)['TemplateBody']
            old_nested_stacks = {}
            resources_response = self._aws_manager.cloudformation_client.describe_stack_resources(StackName=stack_name)
            for resource in resources_response['StackResources']:
                if resource['ResourceType'] == 'AWS::CloudFormation::Stack':
                    m = re.search(r'^.*\/(.*)\/.*$', resource['PhysicalResourceId'])
                    if m:
                        nested_stack_name = m.group(1)
                        old_nested_stacks[nested_stack_name] = self._aws_manager.cloudformation_client.get_template(
                            StackName=nested_stack_name
                        )['TemplateBody']

            print(old_nested_stacks)

            for s, t in environment.get_stack_templates_used(service).items():
                print('================================== ' + s + ' =====================================')
                if 's3_key' in t:
                    filename = t['filename']
                else:
                    template_version = t['version']
                    template_filename = '%s.json' % t['name']
                    user_home_dir = os.path.join(os.path.expanduser('~'), '.nova')
                    filename = os.path.join(user_home_dir, template_version, template_filename)

                print('----------------- ' + s + ' template diff')
                with codecs.open(filename, 'r', 'utf-8') as new_stack_template:
                    print(_udiff.udiff('', new_stack_template.read().replace('\n', '')))

            new_template = service.to_cfn_template(environment, s3_bucket, self._aws_manager)
            print('----------------- parent template diff')
            print(_udiff.udiff(old_template, new_template))

        except ClientError as e:
            raise NovaError(str(e))
        except WaiterError as e:
            raise NovaError(str(e))

