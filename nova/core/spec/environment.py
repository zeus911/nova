from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import json
from collections import OrderedDict

from nova.core.exc import NovaError
from nova.core.spec import resource_name
from nova.core.spec.stack import Stack

from nova.core.cfn_pyplates.core import Resource, JSONableDict, Output
from nova.core.cfn_pyplates.functions import ref


class Environment(object):

    def __init__(self, name, aws_profile, aws_region, resources, deploy_arn, deployment_bucket, deployment_application_id, stacks):
        self.name = name
        self.aws_profile = aws_profile
        self.aws_region = aws_region
        self.resources = resources
        self.deploy_arn = deploy_arn
        self.deployment_bucket = deployment_bucket
        self.deployment_application_id = deployment_application_id
        self.stacks = stacks

    def yaml(self):
        data = OrderedDict([
            ('name', self.name),
            ('aws_profile', self.aws_profile),
            ('aws_region', self.aws_region),
            ('resources', self.resources),
            ('deploy_arn', self.deploy_arn),
            ('deployment_bucket', self.deployment_bucket),
            ('deployment_application_id', self.deployment_application_id),
            ('stacks', [s.yaml() for s in self.stacks])
        ])
        return OrderedDict((k,v) for k,v in data.items() if v is not None)

    def get_stack(self, stack_name):
        stack = next((item for item in self.stacks if item.name == stack_name), None)
        if stack is not None:
            return stack
        else:
            raise NovaError("Stack '%s' was not found in the configuration" % stack_name)

    def get_stack_templates_used(self, service, template_bucket):
        templates_used = dict()
        for s in self.stacks:
            templates_used[s.name] = s.get_template_used(service, template_bucket)
        return templates_used

    def to_cfn_template(self, service, template_bucket, cft, aws_profile):
        extra_resources = self.__read_extra_resources()
        if extra_resources is not None:
            for r in extra_resources:
                cft.resources.add(r)

        codedeploy_app_name = resource_name(service.name + '-Application-Stack')
        cft.resources.add(Resource(codedeploy_app_name, 'AWS::CodeDeploy::Application'))
        cft.outputs.add(Output('CodeDeployApp', ref(codedeploy_app_name)))

        for stack in self.stacks:
            stack.to_cfn_template(service, self, template_bucket, codedeploy_app_name, cft, aws_profile)

    def __read_extra_resources(self):
        if self.resources:
            try:
                with open(self.resources, 'r') as extra_resources_file:
                    rjson = json.load(extra_resources_file)
                    return [JSONableDict(update_dict=r[1], name=r[0]) for r in iter(rjson.items())]
            except IOError:
                raise NovaError("Environment resources '%s' not found." % self.resources)
        else:
            return None

    @staticmethod
    def load(values):
        return Environment(
            values.get("name"),
            values.get("aws_profile"),
            values.get("aws_region"),
            values.get("resources"),
            values.get("deploy_arn"),
            values.get("deployment_bucket"),
            values.get("deployment_application_id"),
            [Stack.load(s) for s in values.get("stacks")]
        )
