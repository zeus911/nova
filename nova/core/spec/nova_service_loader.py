import os
import yaml

from cerberus import Validator

from nova.core import spec
from nova.core.exc import NovaError
from nova.core.spec import yaml_include
from nova.core.spec.service import Service


class NovaServiceLoader:

    def __init__(self, environment=None):
        self.environment = environment
        self.templates_used = dict()
        yaml.add_constructor("!include", yaml_include)

        with open(os.path.join(spec.__path__[0], 'nova_service_schema.yml'), 'r') as schemaYaml:
            schema = yaml.load(schemaYaml)

        v = Validator(schema)
        try:
            with open('nova.yml', 'r') as novaYaml:
                self.service_spec = yaml.safe_load(novaYaml)

            # Validate loaded dictionary
            valid = v.validate(self.service_spec)
            if not valid:
                raise NovaError("Invalid nova.yml file: %s" % v.errors)
            else:
                self.service = Service.load(self.service_spec)
        except IOError:
            raise NovaError("No nova.yml found")

    def set_code_deploy_app(self, environment_name, code_deploy_app_id):
        self.service.set_code_deploy_app(environment_name, code_deploy_app_id)
