"""nova stash controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from cement.core.controller import CementBaseController, expose

from nova.core.managers.manager_provider import ManagerProvider
from nova.core.stash.decrypt import Decrypt
from nova.core.stash.encrypt import Encrypt
from nova.core.exc import NovaError

INCORRECT_GET_ARGS_USAGE = "Usage: nova stash get <environment> <key>"

INCORRECT_PUT_ARGS_USAGE = "Usage: nova stash put <environment> <key> <value>"


class NovaStashController(CementBaseController):
    class Meta:
        label = 'stash'
        description = 'NOVA service stash tools'
        stacked_on = 'base'
        stacked_type = 'nested'
        arguments = [
            (['-p', '--profile'], dict(help='AWS profile')),
            (['-r', '--region'], dict(help='AWS region')),
            (['-b', '--bucket'], dict(help='AWS bucket')),
            (['-k', '--key'], dict(help="AWS KMS Encryption Key Alias. (default is 'novastash')")),
            (['stash_args'], dict(action='store', nargs='*')),
        ]

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()

    @expose(help='Decrypt a service variable')
    def get(self):
        if len(self.app.pargs.stash_args) == 1:
            profile = self.app.pargs.profile
            region = self.app.pargs.region
            bucket = self.app.pargs.bucket
            key = self.app.pargs.stash_args[0]
            manager_provider = ManagerProvider()
            Decrypt(
                stash_key=key,
                manager_provider=manager_provider,
                aws_profile=profile,
                aws_region=region,
                aws_bucket=bucket
            )
        else:
            raise NovaError(INCORRECT_GET_ARGS_USAGE)

    @expose(help='Encrypt a service variable')
    def put(self):
        if len(self.app.pargs.stash_args) == 2:
            profile = self.app.pargs.profile
            region = self.app.pargs.region
            bucket = self.app.pargs.bucket
            kms_key_alias = self.app.pargs.key or 'novastash'
            key = self.app.pargs.stash_args[0]
            value = self.app.pargs.stash_args[1]
            manager_provider = ManagerProvider()
            Encrypt(
                stash_key=key,
                value=value,
                manager_provider=manager_provider,
                aws_profile=profile,
                aws_region=region,
                aws_bucket=bucket,
                kms_key="alias/%s" % kms_key_alias
            )
        else:
            raise NovaError(INCORRECT_PUT_ARGS_USAGE)
