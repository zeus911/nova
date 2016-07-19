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
