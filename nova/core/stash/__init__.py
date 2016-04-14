from botocore.exceptions import ClientError


def check_stash_exists(s3, deployment_bucket_name, key):
    existing_obj=None
    try:
        existing_obj = s3.head_object(Bucket=deployment_bucket_name, Key=key)
    except ClientError:
        pass

    return existing_obj


def kms_key_exists(kms, kms_key):
    return kms.describe_key(KeyId=kms_key) is not None
