from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import git
import time
import boto3
import hashlib
import tempfile
from termcolor import colored
from boto3.s3.transfer import S3Transfer
from botocore.exceptions import ClientError, WaiterError

from nova.core import NovaError
from nova.core import query_yes_no
from nova.core.utils import tarfile_progress as tarfile
from nova.core.utils.s3_progress import ProgressPercentage
from nova.core.utils.cfn_waiter import CloudformationWaiter


class AwsManager(object):

    def __init__(self, profile, region, session=None):
        self.profile = profile
        self.region = region
        # if session:
        #     self._session = session
        # else:
        self._session = boto3.session.Session(profile_name=profile, region_name=region)
        self._account_alias = None
        self._s3_client = None
        self._cf_client = None
        self._cf_resource = None
        self._code_deploy_client = None
        self._iam_client = None
        self._kms_client = None
        self._route53_client = None

    @property
    def account_alias(self):
        if self._account_alias is None:
            self._account_alias = self.iam_client.list_account_aliases()['AccountAliases'][0]
        return self._account_alias

    @property
    def cloudformation(self):
        if self._cf_resource is None:
            self._cf_resource = self._session.resource('cloudformation')
        return self._cf_resource

    @property
    def cloudformation_client(self):
        if self._cf_client is None:
            self._cf_client = self._session.client('cloudformation')
        return self._cf_client

    @property
    def s3_client(self):
        if self._s3_client is None:
            self._s3_client = self._session.client('s3')
        return self._s3_client

    @property
    def code_deploy_client(self):
        if self._code_deploy_client is None:
            self._code_deploy_client = self._session.client('codedeploy')
        return self._code_deploy_client

    @property
    def iam_client(self):
        if self._iam_client is None:
            self._iam_client = self._session.client('iam')
        return self._iam_client

    @property
    def kms_client(self):
        if self._kms_client is None:
            self._kms_client = self._session.client('kms')
        return self._kms_client

    @property
    def route53_client(self):
        if self._route53_client is None:
            self._route53_client = self._session.client('route53')
        return self._route53_client

    def get_hosted_zone_names(self):
        return [z.get('Name') for z in self.route53_client.list_hosted_zones_by_name().get('HostedZones')]

    def create_bucket(self, deployment_bucket_name, msg):
        existing_bucket = None
        try:
            existing_bucket = self.s3_client.head_bucket(Bucket=deployment_bucket_name)
        except ClientError:
            print(colored(msg))
            self.s3_client.create_bucket(Bucket=deployment_bucket_name)
        return existing_bucket

    def s3_put(self, deployment_bucket_name, body, key, meta):
        self.s3_client.put_object(
            Bucket=deployment_bucket_name,
            Body=body,
            Key=key,
            Metadata=meta
        )

    def s3_get(self, deployment_bucket_name, key):
        existing_obj = None
        try:
            existing_obj = self.s3_client.get_object(Bucket=deployment_bucket_name, Key=key)
        except ClientError:
            pass
        return existing_obj

    def s3_head(self, deployment_bucket_name, key):
        existing_obj = None
        try:
            existing_obj = self.s3_client.head_object(Bucket=deployment_bucket_name, Key=key)
        except ClientError:
            pass
        return existing_obj

    def create_stack(self, service_name, cloudformation_template):
        stack_id = self.cloudformation.create_stack(
            StackName=service_name,
            TemplateBody=cloudformation_template,
            Capabilities=["CAPABILITY_IAM"]
        )

        print(colored(stack_id, color='green'))

        waiter = CloudformationWaiter(self.cloudformation)
        print(colored('Cloudformation stack creation in progress. Please check the AWS console!', color='green'))
        print(colored('Waiting on stack creation...', color='magenta'))
        waiter.waiter.wait(StackName=service_name)
        print(colored('Stack creation finished!', color='green'))
        return stack_id

    def get_stack(self, service_name):
        return self.cloudformation.Stack(service_name)

    def update_stack(self, service_name, cloudformation_template, changeset_id, cf_stack):
        try:
            cs_response = self.cloudformation_client.create_change_set(
                StackName=cf_stack.stack_name,
                TemplateBody=cloudformation_template,
                Capabilities=["CAPABILITY_IAM"],
                ChangeSetName=changeset_id
            )
            cs_id = cs_response['Id']
            changes = self.cloudformation_client.describe_change_set(StackName=cf_stack.stack_name, ChangeSetName=cs_id)

            # delay for 2 seconds while waiting for changeset to create
            time.sleep(2)

            print(colored("The following stack update changes to be applied:", 'cyan'))
            print(colored("================================================================================", 'cyan'))
            print(colored(changes, 'yellow'))
            print(colored("================================================================================", 'cyan'))
            perform_update = query_yes_no("Perform changes?")
            if perform_update:
                self.cloudformation_client.execute_change_set(
                    ChangeSetName=changeset_id,
                    StackName=cf_stack.stack_name
                )

                waiter = CloudformationWaiter(self.cloudformation)
                print(colored('Cloudformation stack update in progress. Please check the AWS console!', color='green'))
                print(colored('Waiting on stack update...', color='magenta'))
                waiter.waiter.wait(StackName=service_name)
                print(colored('Stack update finished!', color='green'))
            else:
                self.cloudformation_client.delete_change_set(StackName=cf_stack.stack_name, ChangeSetName=cs_id)
        except ClientError as e:
            raise NovaError(str(e))
        except WaiterError as e:
            raise NovaError(str(e))

    def create_deployment(self, cd_app, cd_deploy_group, revision_etag, deployment_bucket_name, key):
        response = self.code_deploy_client.create_deployment(
            applicationName=cd_app,
            deploymentGroupName=cd_deploy_group,
            revision={
                'revisionType': 'S3',
                's3Location': {
                    'bucket': deployment_bucket_name,
                    'key': key,
                    'bundleType': 'tgz',
                    'eTag': revision_etag
                }
            }
        )
        print(response)
        return response

    def push_revision(self, deployment_bucket_name, key, code_deploy_app, nova_deploy_dir):
        print(colored("Compressing deployment bundle...", color='cyan'))
        # zip entire nova-deploy directory to {app-name}-{build-id}.tar.gz and push to s3
        tmp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".gz", delete=False)
        with tarfile.open(tmp_file.name, 'w:gz') as gz_out:
            for f in os.listdir(nova_deploy_dir):
                gz_out.add(os.path.join(nova_deploy_dir, f), arcname=f, progress=tarfile.progressprint)

        print(colored("Pushing deployment bundle '%s' to S3..." % tmp_file.name, color='green'))

        try:
            transfer = S3Transfer(self.s3_client)
            transfer.upload_file(tmp_file.name, deployment_bucket_name, key, callback=ProgressPercentage(tmp_file.name))
        except ClientError as e:
            if 'AccessDenied' in e.message:
                print(colored("Access denied to upload to '%s/%s'" % (deployment_bucket_name, key), 'red'))
                raise

        os.unlink(tmp_file.name)  # clean up the temp file

        print("")  # Need a new-line after transfer progress
        print(colored("Revision '%s' uploaded to S3 for deployment." % key, color='green'))

        revision_etag = self.s3_head(deployment_bucket_name, key).get('ETag')

        self.code_deploy_client.register_application_revision(
            applicationName=code_deploy_app,
            revision={
                'revisionType': 'S3',
                's3Location': {
                    'bucket': deployment_bucket_name,
                    'key': key,
                    'bundleType': 'tgz',
                    'eTag': revision_etag
                }
            }
        )

        return revision_etag

    def kms_generate_data_key(self, kms_key, context):
        try:
            return self.kms_client.generate_data_key(KeyId=kms_key, EncryptionContext=context, NumberOfBytes=64)
        except:
            raise NovaError("Could not generate key using KMS key %s: %s" % (kms_key, str(sys.exc_info()[0])))

    def kms_key_exists(self, kms_key):
        return self.kms_client.describe_key(KeyId=kms_key) is not None

    def kms_decrypt(self, cipher, context):
        try:
            return self.kms_client.decrypt(CiphertextBlob=cipher, EncryptionContext=context)
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

    def create_and_upload_stack_template(self, s3_bucket, service, environment):
        bucket = self.create_bucket(s3_bucket, 'Common Nova service templates bucket does not exist, creating...')

        for s, template in environment.get_stack_templates_used(service, s3_bucket).items():
            if 's3_key' in template:
                template_file = template['filename']
                template_s3_key = template['s3_key']
            else:
                template_version = template['version']
                template_filename = '%s.json' % template['name']
                user_home_dir = os.path.join(os.path.expanduser('~'), '.nova')

                if not os.path.exists(user_home_dir):
                    raise NovaError("Unable to find NOVA templates. Please create templates under '~/.nova'.")

                repo = git.Repo(user_home_dir)
                # If repo is dirty or has un-pushed commits we want to fail here
                if repo.is_dirty() or bool(repo.git.rev_list("origin/master..master")):
                    raise NovaError("You have local modifications to '~/.nova'. These are shared templates! Please create a pull request!")

                template_file = os.path.join(user_home_dir, template_version, template_filename)
                template_s3_key = '%s/%s' % (template_version, template_filename)

            existing_file = None
            if bucket:
                print(colored('Found common Nova service templates bucket. Verifying contents...', color='cyan'))
                checksum = self.__md5(template_file)
                try:
                    existing_file = self.s3_client.head_object(Bucket=s3_bucket, Key=template_s3_key, IfMatch=checksum)
                except ClientError:
                    pass

            if not existing_file:
                print(colored('Common Nova service templates not found. Uploading...', color='cyan'))
                with open(template_file, 'rb') as template_data:
                    self.s3_client.put_object(Bucket=s3_bucket, Key=template_s3_key, Body=template_data)
                print(colored('Contents uploaded!', color='green'))
            else:
                print(colored('Contents verified!', color='green'))

        print(colored('All required templates have been uploaded & verified!', color='green'))

    @staticmethod
    def __md5(fname):
        md5_hash = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
