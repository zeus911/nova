from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import boto3
from termcolor import colored
from botocore.exceptions import ClientError, WaiterError

from nova.core import query_yes_no, get_git_revision, check_latest_version
from nova.core.stack import create_and_upload_stack_template
from nova.core.exc import NovaError
from nova.core.spec.nova_service_loader import NovaServiceLoader
from nova.core.utils.cfn_waiter import CloudformationWaiter


def green(message):
    return colored(message, color='green')


class UpdateStack:

    def __init__(self, aws_profile, environment_name):
        check_latest_version()
        self.environment_name = environment_name
        print(colored("Creating cloudformation scripts...", color='cyan'))
        self.service = NovaServiceLoader(environment_name)
        self.environment = self.service.service.get_environment(environment_name)
        awsprofile = aws_profile or self.environment.aws_profile
        session = boto3.session.Session(profile_name=awsprofile, region_name=self.environment.aws_region)

        cf_client = session.client('cloudformation')
        cloudformation = session.resource('cloudformation')
        s3 = session.client('s3')
        account_id = session.client('iam').list_account_aliases()['AccountAliases'][0]
        s3_bucket = 'nova-deployment-templates-%s' % account_id

        create_and_upload_stack_template(s3, s3_bucket, self.service.service, self.environment)
        cloudformation_template = self.service.service.to_cfn_template(self.environment, s3_bucket, aws_profile)

        try:
            changeset_id = "cs%s" % get_git_revision().replace(".", "x")

            cf_stack = cloudformation.Stack(self.service.service.name)
            cs_response = cf_client.create_change_set(
                StackName=cf_stack.stack_name,
                TemplateBody=cloudformation_template,
                Capabilities=["CAPABILITY_IAM"],
                ChangeSetName=changeset_id
            )
            cs_id = cs_response['Id']

            changes = cf_client.describe_change_set(StackName=cf_stack.stack_name, ChangeSetName=cs_id)

            # if len(changes) > 0:
            print(colored("The following stack update changes to be applied:", 'cyan'))
            print(colored("================================================================================", 'cyan'))
            print(colored(changes, 'yellow'))
            print(colored("================================================================================", 'cyan'))
            perform_update = query_yes_no("Perform changes?")
            if perform_update:
                self.do_stack_update(cf_stack.stack_name, cs_id, cf_client, cloudformation)
            else:
                cf_client.delete_change_set(StackName=cf_stack.stack_name, ChangeSetName=cs_id)
            # else:
            #     print(colored('No changes to perform!', 'yellow'))
            #     print(colored('Removing empty Changeset...', 'cyan'))
            #     time.sleep(5)  # delays for 5 seconds
            #     cf_client.delete_change_set(StackName=cf_stack.stack_name, ChangeSetName=cs_id)
            #     print(colored('Empty changeset removed.', 'cyan'))
        except ClientError as e:
            raise NovaError(str(e))
        except WaiterError as e:
            raise NovaError(str(e))

    def do_stack_update(self, stack_name, changeset_id, cf_client, cloudformation):
        try:
            cf_client.execute_change_set(
                ChangeSetName=changeset_id,
                StackName=stack_name
            )

            waiter = CloudformationWaiter(cloudformation)
            print(green('Cloudformation stack update in progress. Please check the AWS console!'))
            print(colored('Waiting on stack update...', color='magenta'))
            waiter.waiter.wait(StackName=self.service.service.name)
            print(green('Stack update finished!'))

            stack = cloudformation.Stack(self.service.service.name)
            if stack.stack_status == "UPDATE_COMPLETE":
                if stack.outputs is not None:
                    for output in stack.outputs:
                        if output.get('OutputKey') == 'CodeDeployApp':
                            code_deploy_app_id = output.get('OutputValue')
                            print("Found code-deploy app: %s" % code_deploy_app_id)
                            self.service.set_code_deploy_app(self.environment_name, code_deploy_app_id)
                            print(green("Please update nova.yml environment with 'deployment_application_id' manually."))
                            break

                        for stack in self.environment.stacks:
                            if output.get('OutputKey') == stack.name.title() + 'DeploymentGroup':
                                code_deploy_app_id = output.get('OutputValue')
                                print(colored("Found code-deploy deployment group for stack '%s': %s" % (stack.name, code_deploy_app_id), color='green'))
                                self.service.set_code_deploy_app(self.environment_name, code_deploy_app_id)
                                print(green("Please update nova.yml environment with 'deployment_application_id' manually."))
                            else:
                                print(colored("Unable to find code-deploy deployment group for stack '%s' in the stack output" % stack.name, 'yellow'))
                                print(colored("Please update nova.yml stack with the 'deployment_group' manually.", color='yellow'))

                    else:
                        print(colored('Unable to find code-deploy application in the stack output', 'yellow'))
                        print(colored("Please update nova.yml environment with 'deployment_application_id' manually.", color='yellow'))
                else:
                    print(colored("Please update nova.yml environment with 'deployment_application_id' manually.", color='yellow'))
                    print(colored("and your stacks with their respective 'deployment_group' manually.", color='yellow'))

            else:
                raise NovaError("Stack update was un-successful: %s - %s" % (stack.stack_status, stack.stack_status_reason))
        except ClientError as e:
            raise NovaError(str(e))
        except WaiterError as e:
            raise NovaError(str(e))
