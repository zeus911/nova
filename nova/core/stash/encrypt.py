from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Hash.HMAC import HMAC
from Crypto.Util import Counter
from Crypto.Util.py3compat import tobytes
from termcolor import colored

from nova.core import query_yes_no, check_latest_version
from nova.core.exc import NovaError


class Encrypt:

    def __init__(self, stash_key, value, manager_provider, aws_profile=None, aws_region=None, aws_bucket=None, kms_key='alias/novastash'):
        check_latest_version()

        self._aws_manager = manager_provider.aws_manager(aws_profile, aws_region or 'us-east-1')

        if aws_bucket is None:
            deployment_bucket_name = 'novastash_%s' % self._aws_manager.account_alias
        else:
            deployment_bucket_name = aws_bucket

        if not self._aws_manager.kms_key_exists(kms_key):
            raise NovaError("Please setup the novastash KMS key.")

        self._aws_manager.create_bucket(deployment_bucket_name, "Creating novastash bucket '%s'" % deployment_bucket_name)

        # generate a a 64 byte key.
        # Half will be for data encryption, the other half for HMAC
        kms_response = self._aws_manager.kms_generate_data_key(kms_key, {})

        data_key = tobytes(kms_response['Plaintext'][:32])
        hmac_key = tobytes(kms_response['Plaintext'][32:])
        wrapped_key = tobytes(kms_response['CiphertextBlob'])

        enc_ctr = Counter.new(128)
        encryptor = AES.new(data_key, AES.MODE_CTR, counter=enc_ctr)

        c_text = encryptor.encrypt(tobytes(value))
        # compute an HMAC using the hmac key and the ciphertext
        hmac = HMAC(hmac_key, msg=c_text, digestmod=SHA256)
        b64hmac = hmac.hexdigest()

        key = "%s.txt.enc" % stash_key
        existing_stash = self._aws_manager.s3_head(deployment_bucket_name, key)

        if existing_stash is None:
            print(colored("Stashing '%s'" % stash_key))
            self._aws_manager.s3_put(
                deployment_bucket_name,
                b64encode(c_text).decode('utf-8'),
                key,
                {'encryption-key': b64encode(wrapped_key).decode('utf-8'), 'hmac': b64hmac}
            )
        else:
            perform_overwrite = query_yes_no("Stash '%s' already exists, want to overwrite?" % stash_key, default="no")
            if perform_overwrite:
                self._aws_manager.s3_put(
                    deployment_bucket_name,
                    b64encode(c_text).decode('utf-8'),
                    key,
                    {'encryption-key': b64encode(wrapped_key).decode('utf-8'), 'hmac': b64hmac}
                )
            else:
                print(colored("Not stashing anything for key '%s'" % stash_key))
