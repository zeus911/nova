from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import tempfile
import shutil
import atexit
import yaml
import boto3
from boto3.s3.transfer import S3Transfer
from botocore.exceptions import ClientError
from termcolor import colored
from distutils import dir_util
from docker import Client as DockerClient
from docker.utils import kwargs_from_env
from jinja2 import Template

from nova.core import templates, get_git_revision
from nova.core.deploy import *
from nova.core.exc import NovaError
from nova.core.utils import tarfile_progress as tarfile
from nova.core.spec.nova_service_loader import NovaServiceLoader
from nova.core.utils.s3_progress import ProgressPercentage


class DeployLocalStack:

    def __init__(self, aws_profile, output_dir, ip, environment_name, stack_name, version=None):
        if output_dir is None:
            atexit.register(self.cleanup)

        self.build_id = version if version else get_git_revision()
        print(colored("Creating deployment bundle for revision '%s'..." % self.build_id, color='cyan'))
        self.service_loader = NovaServiceLoader(environment_name)
        self.service = self.service_loader.service
        self.environment = self.service_loader.service.get_environment(environment_name)
        self.stack = self.environment.get_stack(stack_name)

        kwargs = kwargs_from_env()
        kwargs['tls'].assert_hostname = False
        kwargs['version'] = 'auto'
        docker = DockerClient(**kwargs)
        awsprofile = aws_profile or self.environment.aws_profile
        session = boto3.session.Session(profile_name=awsprofile, region_name=self.environment.aws_region)
        codedeploy = session.client('codedeploy')
        s3 = session.client('s3')

        if self.environment.deployment_application_id is None:
            raise NovaError("Environment '%s' does not have 'deployment_application_id' set!" % environment_name)
        self.codedeploy_app = self.environment.deployment_application_id

        deployment_bucket_name = self.environment.deployment_bucket
        key = "%s/%s.tar.gz" % (self.service.name, self.build_id)
        existing_revision = self.check_revision_exists(s3, deployment_bucket_name, key)

        # Create tmp/nova-deploy directory
        self.nova_deploy_dir = output_dir or tempfile.mkdtemp(prefix="%s-nova-deploy-" % self.service.name)
        print(colored("Generating deployment scripts in '%s'..." % self.nova_deploy_dir, color='cyan'))

        docker_image = self.get_docker_image(docker)
        if existing_revision is None:
            print(colored("No existing revision found, creating...", color='magenta'))
            self.create_nova_deploy_dirs()
            self.create_app_spec()
            self.generate_scripts(docker_image)
            self.save_docker_image(docker, docker_image)
            revision_etag = self.push_revision(s3, codedeploy, deployment_bucket_name, key)
            if output_dir is None:
                shutil.rmtree(self.nova_deploy_dir)
        else:
            print(colored("Existing revision found, deploying...", color='green'))
            revision_etag = existing_revision.get('ETag')

        if self.stack.deployment_group is None:
            raise NovaError("Environment '%s' stack '%s' does not have 'deployment_group' set!" % (environment_name, self.stack.name))
        self.codedeploy_deployment_group = self.stack.deployment_group

        if ip is None:
            print(colored("Finding IP addresses to de...", color='cyan'))

        print(colored('CodeDeploy deployment in progress. Please check the AWS console!', color='green'))

    def create_nova_deploy_dirs(self):
        if os.path.exists('nova-deploy'):
            print(colored("Including found service deployment scripts", color='green'))
            dir_util.copy_tree('nova-deploy', self.nova_deploy_dir)

    def create_app_spec(self):
        app_stop_scripts = [
            {'location': 'deregister_from_elb.sh'},
            {'location': 'cleanup_space.sh', 'timeout': 300},
            {'location': 'kill_docker_container.sh', 'timeout': 300}
        ]
        before_install_scripts = []
        after_install_scripts = [
            {'location': 'load_docker_container.sh'}
        ]
        app_start_scripts = [
            {'location': 'start_docker_container.sh', 'timeout': 300},
            {'location': 'register_with_elb.sh'}
        ]
        validate_scripts = [
            {'location': 'validate_service.sh'}
        ]
        app_spec = {
            'version': 0.0,
            'os': 'linux',
            'files': [
                {
                    'source': 'docker/%s-%s-docker-image.tar.gz' % (self.service.name, self.build_id),
                    'destination': '/tmp'
                }
            ],
            'hooks': {
                'ApplicationStop': app_stop_scripts,
                'BeforeInstall': before_install_scripts,
                'AfterInstall': after_install_scripts,
                'ApplicationStart': app_start_scripts,
                'ValidateService': validate_scripts
            }
        }
        with open('%s/appspec.yml' % self.nova_deploy_dir, 'w') as appspecfile:
            yaml.dump(app_spec, appspecfile)

        print(colored("Generated appspec.yml", color='green'))

    def generate_scripts(self, docker_image):
        deploy_scripts_path = os.path.join(templates.__path__[0], 'deploy-scripts')
        for f in os.listdir(deploy_scripts_path):
            file_name = os.path.join(deploy_scripts_path, f)
            shutil.copy(file_name, self.nova_deploy_dir)

        print(colored("Including default common scripts", color='cyan'))

        load_data = {
            'image': docker_image.get("RepoTags")[0],
            'image_filename': '%s-%s-docker-image.tar.gz' % (self.service.name, self.build_id)
        }
        self.render_script('load_docker_container.sh', LOAD_DOCKER_CONTAINER, load_data)
        print(colored("Load docker image script written.", color='green'))

        start_data = {
            'service_name': self.service.name,
            'port': self.service.port,
            'stack_type': self.stack.stack_type,
            'stack_name': self.stack.name,
            'environment_name': self.environment.name,
            'deployment_options': self.stack.deployment_options,
            'deployment_variables': self.stack.deployment_variables,
            'deployment_volumes': self.stack.deployment_volumes,
            'deployment_arguments': self.stack.deployment_arguments,
            'image': docker_image.get("RepoTags")[0]
        }
        self.render_script('start_docker_container.sh', START_DOCKER_CONTAINER, start_data)
        print(colored("Start docker container script written.", color='green'))

        validate_data = {
            'port': self.service.port,
            'healthcheck_url': self.service.healthcheck_url
        }
        self.render_script('validate_service.sh', VALIDATE, validate_data)
        print(colored("Validate service script written.", color='green'))

    def render_script(self, script_filename, template, data):
        script_template = Template(template, trim_blocks=True)
        script_body = str(script_template.render(data)).strip()
        with open(self.nova_deploy_dir + '/' + script_filename, 'w') as script:
            script.write(script_body)

    def save_docker_image(self, docker, docker_image):
        import subprocess
        print(colored("Exporting docker image to include in bundle...", color='cyan'))
        out_file = "%s/docker/%s-%s-docker-image.tar.gz" % (self.nova_deploy_dir, self.service.name, self.build_id)
        dir_util.mkpath("%s/docker" % self.nova_deploy_dir)
        save_cmd = ['docker', 'save', '-o', out_file, docker_image.get("RepoTags")[0]]
        p = subprocess.Popen(save_cmd, stdout=subprocess.PIPE)
        while p.poll() is None:
            print(colored(p.stdout.readline(), color='magenta'))
        print(colored(p.stdout.read(), color='magenta'))

    def push_revision(self, s3, codedeploy, deployment_bucket_name, key):
        print(colored("Compressing deployment bundle...", color='cyan'))
        # zip entire nova-deploy directory to {app-name}-{build-id}.tar.gz and push to s3
        tmp_file = tempfile.NamedTemporaryFile(mode="wb", suffix=".gz", delete=False)
        with tarfile.open(tmp_file.name, 'w:gz') as gz_out:
            for f in os.listdir(self.nova_deploy_dir):
                gz_out.add(os.path.join(self.nova_deploy_dir, f), arcname=f, progress = tarfile.progressprint)

        print(colored("Pushing deployment bundle '%s' to S3..." % tmp_file.name, color='green'))

        transfer = S3Transfer(s3)
        transfer.upload_file(tmp_file.name, deployment_bucket_name, key, callback=ProgressPercentage(tmp_file.name))
        os.unlink(tmp_file.name)  # clean up the temp file

        print("")  # Need a new-line after transfer progress
        print(colored("Revision '%s' uploaded to S3 for deployment." % key, color='green'))

        revision_etag = s3.head_object(Bucket=deployment_bucket_name, Key=key).get('ETag')

        codedeploy.register_application_revision(
            applicationName=self.codedeploy_app,
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

    def get_docker_image(self, docker):
        # Find docker image and 'save' it to {nova_deploy_dir}/docker/image-{build-id}.tar.gz
        looking_for_tag="%s:%s" % (self.service.name, self.build_id)
        matching_images = [d for d in docker.images() if d["RepoTags"][0].endswith(looking_for_tag)]
        if not len(matching_images) == 1:
            raise NovaError("Could not find a docker image with a tag for: '%s'" % looking_for_tag)

        print(colored("Found docker image '%s'." % matching_images[0].get("RepoTags")[0], color='green'))
        return matching_images[0]

    def cleanup(self):
        try:
            if os.path.exists(self.nova_deploy_dir):
                print(colored("Cleaning up deployment bundle...", color='green'))
                shutil.rmtree(self.nova_deploy_dir)
        except Exception as e:
            print(colored(str(e), color='red'))

    @staticmethod
    def check_revision_exists(s3, deployment_bucket_name, key):
        existing_file=None
        try:
            existing_file = s3.head_object(Bucket=deployment_bucket_name, Key=key)
        except ClientError:
            pass

        return existing_file
