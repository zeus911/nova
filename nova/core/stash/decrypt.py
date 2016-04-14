from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from nova.core import check_latest_version
from nova.core.exc import NovaError
from boto3.session import Session
from botocore.exceptions import ClientError
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Hash.HMAC import HMAC
from Crypto.Util import Counter


class Decrypt:

    def __init__(self, stash_key, aws_profile=None, aws_region=None, aws_bucket=None, context=None):
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

        key = "%s.txt.enc" % stash_key
        existing_stash = None
        try:
            existing_stash = s3.get_object(Bucket=deployment_bucket_name, Key=key)
        except ClientError as e:
            pass

        if existing_stash is None:
            raise NovaError("No stash '%s' found!" % stash_key)
        else:
            contents = existing_stash['Body'].read()
            metadata = existing_stash['Metadata']
            encryption_key = metadata['encryption-key']
            try:
                kms_response = kms.decrypt(CiphertextBlob=b64decode(encryption_key), EncryptionContext=context)
            except ClientError as e:
                if e.response["Error"]["Code"] == "InvalidCiphertextException":
                    if context is None:
                        msg = ("Could not decrypt hmac key with KMS. The credential may "
                               "require that an encryption context be provided to decrypt it.")
                    else:
                        msg = ("Could not decrypt hmac key with KMS. The encryption "
                               "context provided may not match the one used when the "
                               "credential was stored.")
                else:
                    msg = "Decryption error %s" % e
                raise NovaError(msg)
            except Exception as e:
                raise NovaError("Decryption error %s" % e)

            key = kms_response['Plaintext'][:32]
            hmac_key = kms_response['Plaintext'][32:]
            hmac = HMAC(hmac_key, msg=b64decode(contents), digestmod=SHA256)
            if hmac.hexdigest() != metadata['hmac']:
                raise NovaError("Computed HMAC on '%s' does not match stored HMAC" % stash_key)
            dec_ctr = Counter.new(128)
            decryptor = AES.new(key, AES.MODE_CTR, counter=dec_ctr)
            value = decryptor.decrypt(b64decode(contents)).decode("utf-8")
            print(value)