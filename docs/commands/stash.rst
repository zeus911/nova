==================
**Stash Commands**
==================

Nova Stash sub-commands provide functionality for storing & retrieving confidential properties in S3 using AWS's KMS encryption/decryption.
Note: These commands do **not** use the `standard AWS API <http://docs.aws.amazon.com/AmazonS3/latest/dev/UsingClientSideEncryption.html>`_ for this, so data stashed with Nova can not be retrieved using the standard AWS API and vice versa.

::

    $ nova stash put '<service-name>.<property key>' '<property value>' --bucket <S3 bucket to use> --profile <profile to use> -k <KMS key alias>

::

    $ nova stash get '<service-name>.<property key>' --bucket <S3 bucket to use>

The 'bucket' parameter has a default value of novastash_<AWS Account Alias>. Nova stash expects a key named novastash in the aws account by default unless told otherwise.

**Example Usage**
-----------------

A minimal example of how to stash and retrieve a database password using the default values for optional command parameters.

::

    $ nova stash put 'test-dashboard.db.password' 'mysupersecretpassword'

::

    $ nova stash get 'test-dashboard.db.password'
