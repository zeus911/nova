==================
**Stash Commands**
==================

Nova Stash sub-commands provide functionality for storing & retrieving confidential properties using AWS's KMS encryption/decryption.

You can stash sensitive properties using KMS & S3 using the stash task: The 'bucket' parameter has a default value
of novastash_<AWS Account Alias>. Nova stash expects a key named novastash in the aws account by default unless told otherwise.

::

    $ nova stash put '<service-name>.<property key>' '<property value>' --bucket <S3 bucket to use> --profile <profile to use> -k <KMS key alias>

::

    $ nova get '<service-name>.<property key>' --bucket <S3 bucket to use>

**Example Usage**
-----------------

Example shows how to stash a database password and retrieve as a Docker environment variable at deployment time.

**NOTE** This example assumes you have the NOVA Tool installed on the server you wish to deploy to.

::

    $ nova stash put 'test-dashboard.db.password' 'mysupersecretpassword' --bucket novastash_data


``nova.yml``

::

    ...
    deployment_variables:
        - DB_PASSWORD: "$(/path/to/nova stash get --bucket novastash_data 'test-service.db.password')"
    ...
