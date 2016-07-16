from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import os
import yaml

from cerberus import Validator

from nova.core import spec
from nova.core.exc import NovaError
from nova.core.spec import yaml_include
from nova.core.spec.service import Service


class NovaServiceLoader:

    def __init__(self, environment_name, nova_descriptor_file=None):
        self._nova_descriptor_file = nova_descriptor_file or 'nova.yml'
        self._environment_name = environment_name
        self._environment = None
        self._codedeploy_app = None

        self.templates_used = dict()
        yaml.add_constructor("!include", yaml_include)

        with open(os.path.join(spec.__path__[0], 'nova_service_schema.yml'), 'r') as schemaYaml:
            schema = yaml.load(schemaYaml)

        v = Validator(schema)
        try:
            with open(self._nova_descriptor_file, 'r') as novaYaml:
                self.service_spec = yaml.safe_load(novaYaml)

            # Validate loaded dictionary
            valid = v.validate(self.service_spec)
            if not valid:
                raise NovaError("Invalid nova service descriptor file '%s': %s" % (self._nova_descriptor_file, v.errors))
            else:
                self.service = Service.load(self.service_spec)
                self.service_name = self.service.name
                self.service_port = self.service.port
                self.service_healthcheck_url = self.service.healthcheck_url
        except IOError:
            raise NovaError("No nova service descriptor found at '%s'" % self._nova_descriptor_file)

    @property
    def environment(self):
        if self._environment is None:
            self._environment = self.service.get_environment(self._environment_name)
        return self._environment

    @property
    def code_deploy_app(self):
        if self.environment.deployment_application_id is None:
            raise NovaError("Environment '%s' does not have 'deployment_application_id' set!" % self._environment_name)

        if self._codedeploy_app is None:
            self._codedeploy_app = self.environment.deployment_application_id
        return self._codedeploy_app

    def get_stack(self, stack_name):
        return self.environment.get_stack(stack_name)

    def set_code_deploy_app(self, environment_name, code_deploy_app_id):
        self.service.set_code_deploy_app(environment_name, code_deploy_app_id)
