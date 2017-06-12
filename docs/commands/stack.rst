==================
**Stack Commands**
==================

Nova Stack sub-commands provide functionality for service infrastructure.

::

    $ nova stack create|update <environment name>

**Note**: You must provide the name of the environment to create.

This task will find any shared templates used by the environment's stacks and ensure they've been uploaded to the
S3 bucket for the AWS account you're using (i.e. "s3://nova-deployment-templates-").
If the templates are already uploaded, Nova will verify that they have no modifications from the version specified
in each stack. Once a stack has been created, you must use the update task or delete it via the AWS console.


Stack: First Time Creation
----------------------------------------

When the Auto Scaling Group (ASG) is created for the first time it defaults to using the application (via the ELB) **Health Check URL**
to verify if the nodes in the ASG are healthy. If a node is not healthy it is pulled down and a new node is started. This
interferes with being able to deploy as the stack constantly cycling. What you have to do is manually change the **Health Check Type**
setting of the ASG to EC2 instead of ELB via the AWS Management Console until you get a good deploy on the nodes (where the application
Health Check URL is returning a 200). This setting is in the following location in the AWS console.

   **EC2** -> **Autoscaling Groups**

   [Select the ASG]

   **Details** tab -> **Edit** -> **Health Check Type**

This config change will check the EC2 Health Check URL to determine if the node is healthy instead, which will stop the ASG
nodes auto-cycling and allow you to deploy unimpeded. After you have successfully deployed you should change back to the **ELB**
Health Check type, so as if an application becomes unhealthy the ASG will kill it and bring up a new one.

Alternatively, you can initially set the ASG Health Check Type to EC2 for your stack in nova.yml:

::

    AutoScalingGroupHealthCheckType: EC2

Once you have successfully deployed a version of your service to the new stack, you can then change this value to ELB and update your stack via the command:

::

    nova stack update
