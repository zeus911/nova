"""nova stash controller."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from cement.core.controller import CementBaseController, expose
from nova.core.stash.decrypt import Decrypt
from nova.core.stash.encrypt import Encrypt
from nova.core.exc import NovaError


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
            Decrypt(key, profile, region, bucket)
        else:
            raise NovaError("Usage: nova stash get <environment> <key>")

    @expose(help='Encrypt a service variable')
    def put(self):
        if len(self.app.pargs.stash_args) == 2:
            profile = self.app.pargs.profile
            region = self.app.pargs.region
            bucket = self.app.pargs.bucket
            key = self.app.pargs.stash_args[0]
            value = self.app.pargs.stash_args[1]
            Encrypt(key, value, profile, region, bucket)
        else:
            raise NovaError("Usage: nova stash put <environment> <key> <value>")
