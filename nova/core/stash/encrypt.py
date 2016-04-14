from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from nova.core import query_yes_no, check_latest_version
from nova.core.stash import check_stash_exists, kms_key_exists
from nova.core.exc import NovaError
from boto3.session import Session
from botocore.exceptions import ClientError
from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Hash.HMAC import HMAC
from Crypto.Util import Counter
from termcolor import colored
import sys


class Encrypt:

    def __init__(self, stash_key, value, aws_profile=None, aws_region=None, aws_bucket=None, kms_key="alias/novastash", context=None):
        check_latest_version()

        if not context:
            context = {}

        awsregion = aws_region or 'us-east-1'
        session = Session(profile_name=aws_profile, region_name=awsregion)

        if aws_bucket is None:
            account_id = session.client('iam').list_account_aliases()['AccountAliases'][0]
            deployment_bucket_name = 'novastash_%s' % account_id
        else:
            deployment_bucket_name = aws_bucket

        s3 = session.client('s3')
        kms = session.client('kms')

        if not kms_key_exists(kms, kms_key):
            raise NovaError("Please setup the novastash KMS key.")

        try:
            s3.head_bucket(Bucket=deployment_bucket_name)
        except ClientError:
            print(colored("Creating novastash bucket '%s'" % deployment_bucket_name))
            s3.create_bucket(Bucket=deployment_bucket_name)

        # generate a a 64 byte key.
        # Half will be for data encryption, the other half for HMAC
        try:
            kms_response = kms.generate_data_key(KeyId=kms_key, EncryptionContext=context, NumberOfBytes=64)
        except:
            raise NovaError("Could not generate key using KMS key %s: %s" % (kms_key, str(sys.exc_info()[0])))
        data_key = kms_response['Plaintext'][:32]
        hmac_key = kms_response['Plaintext'][32:]
        wrapped_key = kms_response['CiphertextBlob']

        enc_ctr = Counter.new(128)
        encryptor = AES.new(data_key, AES.MODE_CTR, counter=enc_ctr)

        c_text = encryptor.encrypt(value)
        # compute an HMAC using the hmac key and the ciphertext
        hmac = HMAC(hmac_key, msg=c_text, digestmod=SHA256)
        b64hmac = hmac.hexdigest()

        key = "%s.txt.enc" % stash_key
        existing_stash = check_stash_exists(s3, deployment_bucket_name, key)

        if existing_stash is None:
            print(colored("Stashing '%s'" % stash_key))
            s3.put_object(
                Bucket=deployment_bucket_name,
                Body=b64encode(c_text).decode('utf-8'),
                Key=key,
                Metadata={
                    'encryption-key': b64encode(wrapped_key).decode('utf-8'),
                    'hmac': b64hmac
                }
            )
        else:
            perform_overwrite = query_yes_no("Stash '%s' already exists, want to overwrite?" % stash_key, default="no")
            if perform_overwrite:
                s3.put_object(
                    Bucket=deployment_bucket_name,
                    Body=b64encode(c_text).decode('utf-8'),
                    Key=key,
                    Metadata={
                        'encryption-key': b64encode(wrapped_key).decode('utf-8'),
                        'hmac': b64hmac
                    }
                )
            else:
                print(colored("Not stashing anything for key '%s'" % stash_key))
