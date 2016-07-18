from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Hash.HMAC import HMAC
from Crypto.Util import Counter

from nova.core import check_latest_version
from nova.core.exc import NovaError


class Decrypt:

    def __init__(self, stash_key, manager_provider, aws_profile=None, aws_region=None, aws_bucket=None):
        check_latest_version()

        self._aws_manager = manager_provider.aws_manager(aws_profile, aws_region or 'us-east-1')

        if aws_bucket is None:
            deployment_bucket_name = 'novastash_%s' % self._aws_manager.account_alias
        else:
            deployment_bucket_name = aws_bucket

        key = "%s.txt.enc" % stash_key
        existing_stash = self._aws_manager.s3_get(deployment_bucket_name, key)

        if existing_stash is None:
            raise NovaError("No stash '%s' found!" % stash_key)
        else:
            contents = existing_stash['Body'].read()
            metadata = existing_stash['Metadata']
            encryption_key = metadata['encryption-key']
            kms_response = self._aws_manager.kms_decrypt(b64decode(encryption_key), {})

            key = kms_response['Plaintext'][:32]
            hmac_key = kms_response['Plaintext'][32:]
            hmac = HMAC(hmac_key, msg=b64decode(contents), digestmod=SHA256)

            if hmac.hexdigest() != metadata['hmac']:
                raise NovaError("Computed HMAC on '%s' does not match stored HMAC" % stash_key)

            dec_ctr = Counter.new(128)
            decryptor = AES.new(key, AES.MODE_CTR, counter=dec_ctr)
            print(decryptor.decrypt(b64decode(contents)).decode("utf-8"))
