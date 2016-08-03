from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from termcolor import colored

from nova.core import check_latest_version
from nova.core.exc import NovaError
from nova.core.managers.version_manager import VersionManager
from nova.core.spec.nova_service_loader import NovaServiceLoader


def green(message):
    return colored(message, color='green')


class UpdateStack:

    def __init__(self, aws_profile, environment_name, manager_provider,
                 cf_template_out=None, nova_descriptor_file=None, include_docker=True):
        check_latest_version()

        print(colored("Creating cloudformation scripts...", color='cyan'))
        self.environment_name = environment_name
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

    def update(self):
        self._aws_manager.create_and_upload_stack_template(self._s3_bucket, self._service_manager.service,
                                                           self._service_manager.environment)
        changeset_id = "cs%s" % VersionManager().current_version().replace(".", "x")
        cf_stack = self._aws_manager.get_stack(self._service_manager.service_name)
        performed_update = self._aws_manager.update_stack(
            self._service_manager.service_name,
            self.cloudformation_template,
            changeset_id,
            cf_stack
        )

        if performed_update:
            stack = self._aws_manager.get_stack(self._service_manager.service_name)
            if stack.stack_status == "UPDATE_COMPLETE":
                if stack.outputs is not None:
                    for output in stack.outputs:
                        if output.get('OutputKey') == 'CodeDeployApp':
                            code_deploy_app_id = output.get('OutputValue')
                            print("Found code-deploy app: %s" % code_deploy_app_id)
                            self._service_manager.service.set_code_deploy_app(self.environment_name, code_deploy_app_id)
                            print(green("Please update nova.yml environment with 'deployment_application_id' manually."))
                            break

                        for stack in self._service_manager.environment.stacks:
                            if output.get('OutputKey') == stack.name.title() + 'DeploymentGroup':
                                code_deploy_app_id = output.get('OutputValue')
                                print(colored("Found code-deploy deployment group for stack '%s': %s" % (
                                    stack.name, code_deploy_app_id), color='green'))
                                self._service_manager.service.set_code_deploy_app(self.environment_name, code_deploy_app_id)
                                print(green("Please update nova.yml environment with 'deployment_application_id' manually."))
                            else:
                                print(colored(
                                    "Unable to find code-deploy deployment group for stack '%s' in the stack output" % stack.name,
                                    'yellow'))
                                print(colored("Please update nova.yml stack with the 'deployment_group' manually.",
                                              color='yellow'))

                    else:
                        print(colored('Unable to find code-deploy application in the stack output', 'yellow'))
                        print(colored("Please update nova.yml environment with 'deployment_application_id' manually.",
                                      color='yellow'))
                else:
                    print(colored("Please update nova.yml environment with 'deployment_application_id' manually.",
                                  color='yellow'))
                    print(colored("and your stacks with their respective 'deployment_group' manually.", color='yellow'))

            else:
                raise NovaError("Stack update was un-successful: %s - %s" % (stack.stack_status, stack.stack_status_reason))
