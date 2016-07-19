===================
**Deploy Commands**
===================

Nova Deploy sub-commands provide functionality for deploying your service to your service infrastructure.

::

    $ nova deploy <environment> <stack> (<version>)?

**Note**: You must provide the name of the environment and stack to deploy.

**Note**: To rollback a bad version, deploy the previous version.

This task will compile the CodeDeploy revision bundle and include the exported Docker image.
Default scripts are included which handle ELB draining and registration during deployment, as well as validation the
service is up and running. The revision bundle is uploaded to the environment's S3 bucket if it's not already found.
CodeDeploy is triggered once the revision has been registered with the specified environment's CodeDeploy application.
