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

    def __init__(self, environment=None, nova_descriptor_file=None):
        if nova_descriptor_file is None:
            nova_descriptor_file = "nova.yml"

        self.environment = environment
        self.templates_used = dict()
        yaml.add_constructor("!include", yaml_include)

        with open(os.path.join(spec.__path__[0], 'nova_service_schema.yml'), 'r') as schemaYaml:
            schema = yaml.load(schemaYaml)

        v = Validator(schema)
        try:
            with open(nova_descriptor_file, 'r') as novaYaml:
                self.service_spec = yaml.safe_load(novaYaml)

            # Validate loaded dictionary
            valid = v.validate(self.service_spec)
            if not valid:
                raise NovaError("Invalid nova service descriptor file '%s': %s" % (nova_descriptor_file, v.errors))
            else:
                self.service = Service.load(self.service_spec)
        except IOError:
            raise NovaError("No nova service descriptor found at '%s'" % nova_descriptor_file)

    def set_code_deploy_app(self, environment_name, code_deploy_app_id):
        self.service.set_code_deploy_app(environment_name, code_deploy_app_id)
