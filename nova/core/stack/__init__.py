from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import os
import hashlib
from botocore.exceptions import ClientError
from termcolor import colored

from nova.core.exc import NovaError


def create_and_upload_stack_template(s3, s3_bucket, service, environment):
    bucket=None
    try:
        bucket = s3.head_bucket(Bucket=s3_bucket)
    except ClientError:
        print(colored('Common Nova service templates bucket does not exist, creating...', color='cyan'))
        s3.create_bucket(Bucket=s3_bucket)

    for s, template in environment.get_stack_templates_used(service, s3_bucket).items():
        if 's3_key' in template:
            template_file = template['filename']
            template_s3_key = template['s3_key']
        else:
            template_version=template['version']
            template_filename='%s.json' % template['name']
            user_home_dir = os.path.join(os.path.expanduser('~'), '.nova')

            if not os.path.exists(user_home_dir):
                raise NovaError("Unable to find NOVA templates. Please create templates under '~/.nova'.")

            template_file = os.path.join(user_home_dir, template_version, template_filename)
            template_s3_key = '%s/%s' % (template_version, template_filename)

        existing_file=None
        if bucket:
            print(colored('Found common Nova service templates bucket. Verifying contents...', color='cyan'))
            checksum = md5(template_file)
            try:
                existing_file = s3.head_object(Bucket=s3_bucket, Key=template_s3_key, IfMatch=checksum)
            except ClientError:
                pass

        if not existing_file:
            print(colored('Common Nova service templates not found. Uploading...', color='cyan'))
            with open(template_file, 'rb') as template_data:
                s3.put_object(Bucket=s3_bucket, Key=template_s3_key, Body=template_data)
            print(colored('Contents uploaded!', color='green'))
        else:
            print(colored('Contents verified!', color='green'))

    print(colored('All required templates have been uploaded & verified!', color='green'))


def md5(fname):
    md5_hash = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()
