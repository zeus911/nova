=================
**Configuration**
=================

Nova uses a YAML file to learn about your service and know how to stand up environments and deploy stacks.
By default Nova looks for the service descriptor in a ``nova.yml`` file at the root of your service.
The root of the Nova service descriptor is the service level and describes some essential service details.

A full description of the options can be found `here <https://github.com/gilt/nova/blob/master/nova/core/spec/nova_service_schema.yml>`_.

There are a few fields that should initially be unpopulated until the stack is created. Those are:

- deployment_application_id
- deployment_group


**Service Details**
===================

- ``service_name`` - The service_name field must match the name of your service's Docker image.
- ``team_name`` - The owning team, used for AWS resource tagging.
- ``port`` - The port your service is exposed on from your Docker image.
- ``healthcheck_url`` - The URL that will be used in the ELB & service validation after deployment. Must return a HTTP 200.
- ``logs`` - See Service Log details below.
- ``environments`` - See Environment details below.


**Service Log details**
=======================

This is a YAML description of cloudwatch log groups. Please see the `CloudWatch Logs Agent Reference <http://docs.aws.amazon.com/AmazonCloudWatch/latest/DeveloperGuide/AgentReference.html>`_ for more details.

- ``file`` - Specifies log files that you want to push to CloudWatch Logs.
- ``group_name`` - Specifies the destination log group. A log group will be created automatically if it doesn't already exist.
- ``datetime_format`` - Specifies how the timestamp is extracted from logs.


**Environment details**
=======================

A service has at least one Environment. An environment is at an AWS account-level and can be thought of as a CodeDeploy application.

Example: A service can have a production environment of 3 production instances and a live-canary instance. In this case
all 4 instances are in the same AWS account, therefore live under one Nova Environment. Each group of instances are a
stack in that Nova Environment.

- ``name`` - The environment name, can be whatever you want, but unique.
- ``aws_profile`` - The local profile to use from your AWS CLI configuration.
- ``aws_region`` - The region to use for this environment, 'us-east-1' is fine for almost every service.
- ``resources`` - A filename. Extra Cloudformation resources to include, if using a standard template, can be supplemented via this (e.g. Redis cluster).
- ``deploy_arn`` - The AWS ARN of a Role to be used by CodeDeploy for deployment.
- ``deployment_bucket`` - The name of an S3 bucket to use for CodeDeploy revisions.
- ``deployment_application_id`` - The CodeDeploy application resource ID.
- ``stacks`` - A list of stacks. See Stack details below.

**Stack details**
=================

An environment has at least one Stack. A stack can be thought of as a CodeDeploy deployment group.

- ``stack_name`` - The stack name, can be whatever you want, but must be unique.
- ``stack_type`` - The type of stack (production, live-canary, staging, sandbox, etc.), used to separate the application environment specific configuration. Becomes a tag on the instance.
- ``stack_custom_template`` - A custom Cloudformation template file name.
- ``stack_template`` - The shared template to be used from ~/.nova/<stack_template_version>/<stack_template>.json
- ``stack_template_version`` - The version of the shared template, the sub-directory inside ~/.nova to use.
- ``stack_deploy_config`` - The CodeDeploy deployment config (e.g. OneAtATime, AllAtOnce or HalfAtATime) created externally to Nova.
- ``deployment_group`` - The CodeDeploy deployment group resource ID.
- ``deployment_options`` - Options provided to the Docker run command
- ``deployment_volumes`` - Volumes provided to the Docker run command
- ``deployment_variables`` - Environment variables provided to the Docker run command
- ``deployment_arguments`` - Arguments provided to the Docker run command

At this level you can add extra attributes to a stack, anything that does not begin with ``stack_`` or ``deployment_`` will be
passed down to your Cloudformation templates as Parameters.


**Minimum Example**
===================

``nova.yml``

::

    service_name: example-service
    team_name: nova
    port: 80
    healthcheck_url: /healthcheck

    environments:
      - name: example-service-environment
        aws_profile: my-aws-credentials-profile
        aws_region: us-east-1
        deploy_arn: arn:aws:iam::012345678912:role/my-code-deploy-role
        deployment_bucket: my-bucket-where-codedeploy-revisions-go
        deployment_application_id: some-codedeploy-app-id
        stacks:
          - stack_name: example-service-environment-stack
            stack_type: prod-stack
            stack_deploy_config: OneAtATime
            deployment_group: some-codedeploy-deployment-group-id

