from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from botocore.exceptions import ClientError, WaiterError
from termcolor import colored

from nova.core import check_latest_version
from nova.core.exc import NovaError
from nova.core.spec.nova_service_loader import NovaServiceLoader


class CreateStack:

    def __init__(self, aws_profile, environment_name, manager_provider,
                 cf_template_out=None, nova_descriptor_file=None, include_docker=True):
        check_latest_version()

        print("Creating cloudformation scripts...")

        self._environment_name = environment_name
        self._service_manager = NovaServiceLoader(environment_name, nova_descriptor_file)
        self._aws_manager = manager_provider.aws_manager(
            aws_profile or self._service_manager.environment.aws_profile,
            self._service_manager.environment.aws_region
        )

        self._s3_bucket = 'nova-deployment-templates-%s' % self._aws_manager.account_alias
        self.cloudformation_template = self._service_manager.service.to_cfn_template(
            self._service_manager.environment,
            self._s3_bucket,
            self._aws_manager,
            cf_template_out,
            include_docker
        )

    def create(self):
        try:
            self._aws_manager.create_and_upload_stack_template(self._s3_bucket, self._service_manager.service, self._service_manager.environment)

            self._aws_manager.create_stack(
                self._service_manager.service_name,
                self.cloudformation_template
            )

            stack = self._aws_manager.get_stack(self._service_manager.service_name)

            if stack.stack_status == "CREATE_COMPLETE":
                if stack.outputs is not None:
                    for output in stack.outputs:
                        if output.get('OutputKey') == 'CodeDeployApp':
                            code_deploy_app_id = output.get('OutputValue')
                            print(colored("Found code-deploy app: %s" % code_deploy_app_id, color='green'))
                            self._service_manager.service.set_code_deploy_app(self._environment_name, code_deploy_app_id)
                            print(colored("Please update nova.yml environment with 'deployment_application_id' manually.", color='yellow'))
                            break

                        for stack in self._service_manager.environment.stacks:
                            if output.get('OutputKey') == stack.name.title() + 'DeploymentGroup':
                                code_deploy_app_id = output.get('OutputValue')
                                print(colored("Found code-deploy deployment group for stack '%s': %s" % (stack.name, code_deploy_app_id), color='green'))
                                self._service_manager.service.set_code_deploy_app(self._environment_name, code_deploy_app_id)
                                print(colored("Please update nova.yml environment with 'deployment_application_id' manually.", color='yellow'))
                            else:
                                print(colored("Unable to find code-deploy deployment group for stack '%s' in the stack output" % stack.name, 'yellow'))
                                print(colored("Please update nova.yml stack with the 'deployment_group' manually.", color='yellow'))

                    else:
                        print(colored('Unable to find code-deploy application in the stack output', 'yellow'))
                        print(colored("Please update nova.yml environment with 'deployment_application_id'", color='yellow'))
                        print(colored("and your stacks with their respective 'deployment_group' manually.", color='yellow'))
                else:
                    print(colored("Please update nova.yml environment with 'deployment_application_id'", color='yellow'))
                    print(colored("and your stacks with their respective 'deployment_group' manually.", color='yellow'))

            else:
                raise NovaError("Stack creation was un-successful: %s" % stack.stack_status_reason)
        except ClientError as e:
            raise NovaError(str(e))
        except WaiterError as e:
            raise NovaError(str(e))
