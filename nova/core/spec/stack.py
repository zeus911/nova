from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import base64
import pickle
from collections import OrderedDict
import boto3
from nova.core.cfn_pyplates.core import Resource, Output
from nova.core.cfn_pyplates.functions import ref, get_att


def stack_param_known(k):
    return k.startswith('stack_') or k.startswith('deployment_')


class Stack(object):
    base_template_url='https://s3.amazonaws.com/%s/%s/%s.json'
    base_custom_template_url='https://s3.amazonaws.com/%s/%s/%s_%s'

    def __init__(self, name, stack_type, custom_template, template, template_version, deploy_config, deployment_options,
                 deployment_volumes, deployment_variables, deployment_arguments, deployment_group, extra_parameters):
        self.name = name
        self.stack_type = stack_type
        self.custom_template = custom_template
        self.template = template
        self.template_version = template_version
        self.deploy_config = deploy_config
        self.deployment_options = deployment_options
        self.deployment_volumes = deployment_volumes
        self.deployment_variables = deployment_variables
        self.deployment_arguments = deployment_arguments
        self.deployment_group = deployment_group
        self.extra_parameters = extra_parameters

    def yaml(self):
        data = OrderedDict([
            ('stack_name', self.name),
            ('stack_type', self.stack_type),
            ('stack_custom_template', self.custom_template),
            ('stack_template', self.template),
            ('stack_template_version', self.template_version),
            ('stack_deploy_config', self.deploy_config),
            ('deployment_options', self.deployment_options),
            ('deployment_volumes', self.deployment_volumes),
            ('deployment_variables', self.deployment_variables),
            ('deployment_arguments', self.deployment_arguments),
            ('deployment_group', self.deployment_group)
        ])
        data.update(self.extra_parameters)
        return OrderedDict((k,v) for k,v in data.items() if v is not None)

    def to_cfn_template(self, service, environment, template_bucket, codedeploy_app_name, cft, aws_profile):
        self.__add_stack(cft, service, environment, template_bucket, aws_profile)
        self.__add_deployment_group(cft, codedeploy_app_name, environment.deploy_arn)

    def __add_stack(self, cft, service, environment, template_bucket, aws_profile):
        other_params = self.extra_parameters.copy()

        if 'DNS' in other_params and other_params.get('HostedZoneName') is None:
            record = other_params.get('DNS')
            awsprofile = aws_profile or environment.aws_profile
            session = boto3.session.Session(profile_name=awsprofile, region_name=environment.aws_region)
            route53 = session.client('route53')
            hostedzones = [z.get('Name') for z in route53.list_hosted_zones_by_name().get('HostedZones')]
            hostedzone = next((z for z in hostedzones if (z in record) or (z[:len(z)-1] in record)), None)
            other_params['HostedZoneName'] = hostedzone

        other_params.update([
            ('StackType', self.stack_type),
            ('Port', service.port),
            ('ApplicationName', service.name),
            ('TeamName', service.team_name),
            ('HealthcheckUrl', service.healthcheck_url),
            ('LogsList', self.serialize_logs_settings(service.logs)),
            ('DockerDeploymentOptions', self.pickle_encode(self.deployment_options)),
            ('DockerDeploymentVariables', self.pickle_encode(self.deployment_variables)),
            ('DockerDeploymentVolumes', self.pickle_encode(self.deployment_volumes)),
            ('DockerDeploymentArguments', self.pickle_encode(self.deployment_arguments))
        ])
        parameters = {
            'TemplateURL': self.template_url_to_use(service, template_bucket),
            'TimeoutInMinutes': 60,
            'Parameters': other_params
        }
        cft.resources.add(Resource(self.name.title(), 'AWS::CloudFormation::Stack', parameters))

    def __add_deployment_group(self, cft, codedeploy_app_name, deploy_arn):
        parameters = {
            'ApplicationName': ref(codedeploy_app_name),
            'AutoScalingGroups': [get_att(self.name.title(), 'Outputs.AutoScalingGroup')],
            'DeploymentConfigName': 'CodeDeployDefault.%s' % self.deploy_config,
            'ServiceRoleArn': deploy_arn
        }
        deployment_group_name = self.name.title() + 'DeploymentGroup'
        cft.resources.add(Resource(deployment_group_name, 'AWS::CodeDeploy::DeploymentGroup', parameters))
        cft.outputs.add(Output(deployment_group_name, ref(deployment_group_name)))

    def get_template_used(self, service, template_bucket):
        if self.custom_template is not None:
            return {'filename': self.custom_template, 's3_key': '%s/%s_%s' % (service.name, self.name, self.custom_template)}
        else:
            return {'name': self.template, 'version': self.template_version}

    def template_url_to_use(self, service, template_bucket):
        if self.custom_template is not None:
            return self.base_custom_template_url % (template_bucket, service.name, self.name, self.custom_template)
        else:
            return self.base_template_url % (template_bucket, self.template_version, self.template)

    @staticmethod
    def load(values):
        extra_parameters = dict([(k, v) for (k, v) in values.items() if not stack_param_known(k)])
        return Stack(
            values.get("stack_name"),
            values.get('stack_type'),
            values.get('stack_custom_template'),
            values.get("stack_template"),
            values.get("stack_template_version"),
            values.get("stack_deploy_config"),
            values.get("deployment_options"),
            values.get("deployment_volumes"),
            values.get("deployment_variables"),
            values.get("deployment_arguments"),
            values.get("deployment_group"),
            extra_parameters
        )

    @staticmethod
    def stack_param_known(k):
        return k.startswith('stack_') or k.startswith('deployment_')

    def serialize_logs_settings(self, logs):
        if logs is not None:
            log_list = [l.yaml() for l in logs]
            return self.pickle_encode(log_list)
        else:
            return base64.b64encode(pickle.dumps([]))

    @staticmethod
    def pickle_encode(to_pickle):
        if to_pickle is not None:
            return base64.b64encode(pickle.dumps(to_pickle))
        else:
            return base64.b64encode(pickle.dumps([]))
