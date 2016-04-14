from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import boto3
from termcolor import colored
from botocore.exceptions import ClientError, WaiterError

from nova.core import check_latest_version
from nova.core.stack import create_and_upload_stack_template
from nova.core.exc import NovaError
from nova.core.spec.nova_service_loader import NovaServiceLoader
from nova.core.utils.cfn_waiter import CloudformationWaiter


class CreateStack:

    def __init__(self, aws_profile, environment_name):
        check_latest_version()
        print("Creating cloudformation scripts...")
        service = NovaServiceLoader(environment_name)
        environment = service.service.get_environment(environment_name)
        awsprofile = aws_profile or environment.aws_profile
        session = boto3.session.Session(profile_name=awsprofile, region_name=environment.aws_region)

        cloudformation = session.resource('cloudformation')
        s3 = session.client('s3')
        account_id = session.client('iam').list_account_aliases()['AccountAliases'][0]
        s3_bucket = 'nova-deployment-templates-%s' % account_id

        create_and_upload_stack_template(s3, s3_bucket, service.service, environment)
        cloudformation_template = service.service.to_cfn_template(environment, s3_bucket, aws_profile)

        try:
            stack_id = cloudformation.create_stack(
                StackName=service.service.name,
                TemplateBody=cloudformation_template,
                Capabilities=["CAPABILITY_IAM"]
            )
            print(colored(stack_id, color='green'))

            waiter = CloudformationWaiter(cloudformation)
            print(colored('Cloudformation stack creation in progress. Please check the AWS console!', color='green'))
            print(colored('Waiting on stack creation...', color='magenta'))
            waiter.waiter.wait(StackName=service.service.name)
            print(colored('Stack creation finished!', color='green'))

            stack = cloudformation.Stack(service.service.name)
            if stack.stack_status == "CREATE_COMPLETE":
                if stack.outputs is not None:
                    for output in stack.outputs:
                        if output.get('OutputKey') == 'CodeDeployApp':
                            code_deploy_app_id = output.get('OutputValue')
                            print(colored("Found code-deploy app: %s" % code_deploy_app_id, color='green'))
                            service.set_code_deploy_app(environment_name, code_deploy_app_id)
                            print(colored("Please update nova.yml environment with 'deployment_application_id' manually.", color='yellow'))
                            break

                        for stack in environment.stacks:
                            if output.get('OutputKey') == stack.name.title() + 'DeploymentGroup':
                                code_deploy_app_id = output.get('OutputValue')
                                print(colored("Found code-deploy deployment group for stack '%s': %s" % (stack.name, code_deploy_app_id), color='green'))
                                service.set_code_deploy_app(environment_name, code_deploy_app_id)
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

