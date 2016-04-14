from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from collections import OrderedDict
import pyaml
from nova.core.cfn_pyplates.core import CloudFormationTemplate
from nova.core.exc import NovaError
from nova.core.spec.environment import Environment
from nova.core.spec.service_log_mapping import ServiceLogMapping


class Service(object):

    def __init__(self, name, team_name, port, healthcheck_url, logs, environments):
        self.name = name
        self.team_name = team_name
        self.port = port
        self.healthcheck_url = healthcheck_url
        self.logs = logs
        self.environments = environments

    def yaml(self):
        logs_list = None
        if self.logs is not None:
            logs_list = [lm.yaml() for lm in self.logs]

        data = OrderedDict([
            ('service_name', self.name),
            ('team_name', self.team_name),
            ('port', self.port),
            ('healthcheck_url', self.healthcheck_url),
            ('logs', logs_list),
            ('environments', [e.yaml() for e in self.environments])
        ])
        return pyaml.dump(OrderedDict((k,v) for k,v in data.items() if v is not None))

    def get_environment(self, environment_name):
        environment = next((item for item in self.environments if item.name == environment_name), None)
        if environment is not None:
            return environment
        else:
            raise NovaError("Environment '%s' was not found in the configuration" % environment_name)

    def set_code_deploy_app(self, environment_name, code_deploy_app_id):
        self.get_environment(environment_name).deployment_application_id = code_deploy_app_id

    def to_cfn_template(self, environment, template_bucket, aws_profile):
        description = "%s %s %s stack" % (self.team_name, self.name, environment.name)
        cfn = CloudFormationTemplate(description=description)
        environment.to_cfn_template(self, template_bucket, cfn, aws_profile)
        json_cfn = cfn.json

        # if query_yes_no("Output Cloudformation to nova-cloudformation.json?"):
        #     with open('nova-cloudformation.json', 'w') as out_json:
        #         out_json.write(json.dumps(json.loads(json_cfn), indent=2))

        return json_cfn

    @staticmethod
    def load(values):
        logs_list = values.get("logs")
        if logs_list is not None:
            logs_list = [ServiceLogMapping.load(lm) for lm in logs_list]

        return Service(
            values.get("service_name"),
            values.get("team_name"),
            values.get("port"),
            values.get("healthcheck_url"),
            logs_list,
            [Environment.load(e) for e in values.get("environments")]
        )
