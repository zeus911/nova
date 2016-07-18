from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import yaml
import atexit
import shutil
import tempfile
from jinja2 import Template
from termcolor import colored
from distutils import dir_util
from os.path import isfile, join

from nova.core import templates, check_latest_version
from nova.core.deploy import LOAD_DOCKER_CONTAINER, START_DOCKER_CONTAINER, VALIDATE
from nova.core.exc import NovaError
from nova.core.spec.custom_scripts import CustomScripts
from nova.core.spec.nova_service_loader import NovaServiceLoader


class DeployStack:

    def __init__(self, environment_name, stack_name, aws_profile, manager_provider,
                 version=None, deploy=True, nova_descriptor_file=None):
        self._environment_name = environment_name
        self._stack_name = stack_name
        self._deploy = deploy
        self._version_manager = manager_provider.version_manager()
        self._docker_manager = manager_provider.docker_manager()
        self._service_manager = NovaServiceLoader(environment_name, nova_descriptor_file)
        self._aws_manager = manager_provider.aws_manager(
            aws_profile or self._service_manager.environment.aws_profile,
            self._service_manager.environment.aws_region
        )
        self._build_id = self._version_manager.current_version(version)
        self._stack = self._service_manager.get_stack(self._stack_name)
        self._code_deploy_app = self._service_manager.code_deploy_app
        if self._stack.deployment_group is None:
            raise NovaError("Environment '%s' stack '%s' does not have 'deployment_group' set!" % (
                self._environment_name, self._stack.name))

        self._nova_deploy_dir = None
        self._custom_scripts = CustomScripts()

    def deploy(self):
        atexit.register(self.__cleanup)
        check_latest_version()

        print("Deploying to account '%s'..." % self._aws_manager.account_alias)
        print(colored("Creating deployment bundle for revision '%s'..." % self._build_id, color='cyan'))

        deployment_bucket_name = self._service_manager.environment.deployment_bucket
        key = "%s/%s.tar.gz" % (self._service_manager.service_name, self._build_id)
        existing_revision = self._aws_manager.s3_head(deployment_bucket_name, key)

        # Create tmp/nova-deploy directory
        self._nova_deploy_dir = tempfile.mkdtemp(prefix="%s-nova-deploy-" % self._service_manager.service_name)

        if existing_revision is None:
            revision_etag = self.__build_upload_revision(deployment_bucket_name, key)
        else:
            print(colored("Existing revision found, deploying...", color='green'))
            revision_etag = existing_revision.get('ETag')

        print(colored("Triggering code-deploy...", color='cyan'))

        if self._deploy:
            self._aws_manager.create_deployment(
                self._code_deploy_app,
                self._stack.deployment_group,
                revision_etag,
                deployment_bucket_name,
                key
            )
            print(colored('CodeDeploy deployment in progress. Please check the AWS console!', color='green'))
        else:
            print(colored('Deployment not triggered, S3 revision uploaded and registered with CodeDeploy.', color='yellow'))

    def __build_upload_revision(self, deployment_bucket_name, key):
        print(colored("No existing revision found, creating...", color='magenta'))
        print(colored("Generating deployment scripts in '%s'..." % self._nova_deploy_dir, color='cyan'))
        self.__create_nova_deploy_dirs()
        self.__create_app_spec()
        # Find docker image and 'save' it to {nova_deploy_dir}/docker/image-{build-id}.tar.gz
        looking_for_tag = "%s:%s" % (self._service_manager.service_name, self._build_id)
        out_file = "%s/docker/%s-%s-docker-image.tar.gz" % (
            self._nova_deploy_dir, self._service_manager.service_name, self._build_id)
        dir_util.mkpath("%s/docker" % self._nova_deploy_dir)
        docker_image = self._docker_manager.save_docker_image_with_tag(looking_for_tag, out_file)
        self.__generate_scripts(docker_image)
        revision_etag = self._aws_manager.push_revision(deployment_bucket_name, key, self._code_deploy_app, self._nova_deploy_dir)
        shutil.rmtree(self._nova_deploy_dir)
        return revision_etag

    def __create_nova_deploy_dirs(self):
        if os.path.exists('nova-scripts'):
            print(colored("Including found custom service deployment scripts", color='green'))
            self._custom_scripts.app_stop_scripts = self.__copy_custom_scripts('nova-scripts/ApplicationStop')
            self._custom_scripts.before_install_scripts = self.__copy_custom_scripts('nova-scripts/BeforeInstall')
            self._custom_scripts.after_install_scripts = self.__copy_custom_scripts('nova-scripts/AfterInstall')
            self._custom_scripts.app_start_scripts = self.__copy_custom_scripts('nova-scripts/ApplicationStart')
            self._custom_scripts.validate_scripts = self.__copy_custom_scripts('nova-scripts/ValidateService')

    def __copy_custom_scripts(self, path_dir):
        if os.path.exists(path_dir):
            dir_util.copy_tree(path_dir, self._nova_deploy_dir)
            return [f for f in os.listdir(path_dir) if isfile(join(path_dir, f))]
        else:
            return []

    def __create_app_spec(self):
        os.mkdir(os.path.join(self._nova_deploy_dir, 'env-vars'))
        files = [
            {
                'source': 'docker/%s-%s-docker-image.tar.gz' % (self._service_manager.service_name, self._build_id),
                'destination': '/tmp'
            }
        ]

        for stack in self._service_manager.environment.stacks:
            os.mkdir(os.path.join(self._nova_deploy_dir, 'env-vars/%s' % stack.stack_type))
            files.extend(self.__render_stack_files(stack))

        app_stop_scripts = [{'location': 'cleanup_space.sh', 'timeout': 300}]
        app_stop_scripts.extend(self._custom_scripts.app_stop_scripts_for_app_spec)

        before_install_scripts = [
            {'location': 'deregister_from_elb.sh'},
            {'location': 'kill_docker_container.sh', 'timeout': 300}
        ]
        before_install_scripts.extend(self._custom_scripts.before_install_scripts_for_app_spec)

        after_install_scripts = [{'location': 'load_docker_container.sh'}]
        after_install_scripts.extend(self._custom_scripts.after_install_scripts_for_app_spec)

        app_start_scripts = [
            {'location': 'start_docker_container.sh', 'timeout': 300},
            {'location': 'register_with_elb.sh'}
        ]
        app_start_scripts.extend(self._custom_scripts.app_start_scripts_for_app_spec)

        validate_scripts = [{'location': 'validate_service.sh'}]
        validate_scripts.extend(self._custom_scripts.validate_scripts_for_app_spec)

        app_spec = {
            'version': 0.0,
            'os': 'linux',
            'files': files,
            'hooks': {
                'ApplicationStop': app_stop_scripts,
                'BeforeInstall': before_install_scripts,
                'AfterInstall': after_install_scripts,
                'ApplicationStart': app_start_scripts,
                'ValidateService': validate_scripts
            }
        }
        with open('%s/appspec.yml' % self._nova_deploy_dir, 'w') as appspecfile:
            yaml.dump(app_spec, appspecfile)

        print(colored("Generated appspec.yml", color='green'))

    def __render_stack_files(self, stack):
        deployment_options = ''
        if stack.deployment_options is not None:
            for opts in stack.deployment_options:
                for args in opts.items():
                    deployment_options += "{0}={1} ".format(args[0], args[1])
            deployment_options += "\n"
        self.__render_file('env-vars/%s/docker-opts.list' % stack.stack_type, deployment_options.strip())

        deployment_volumes = ''
        if stack.deployment_volumes is not None:
            for opts in stack.deployment_volumes:
                for args in opts.items():
                    deployment_volumes += "-v {0}:{1} ".format(args[0], args[1])
            deployment_volumes += "\n"
        self.__render_file('env-vars/%s/docker-vols.list' % stack.stack_type, deployment_volumes.strip())

        deployment_variables = ''
        if stack.deployment_variables is not None:
            for opts in stack.deployment_variables:
                for args in opts.items():
                    deployment_variables += '-e "{0}={1}"\n'.format(args[0], args[1])
            deployment_variables += "\n"
        self.__render_file('env-vars/%s/docker-vars.list' % stack.stack_type, deployment_variables.strip())

        deployment_arguments = ''
        if stack.deployment_arguments is not None:
            for opts in stack.deployment_arguments:
                for args in opts.items():
                    deployment_arguments += "{0}={1} ".format(args[0], args[1])
            deployment_arguments += "\n"
        self.__render_file('env-vars/%s/docker-args.list' % stack.stack_type, deployment_arguments.strip())

        return [{
            'source': 'env-vars/%s/docker-opts.list' % stack.stack_type,
            'destination': '/opt/nova/environments/%s' % stack.stack_type
        }, {
            'source': 'env-vars/%s/docker-vols.list' % stack.stack_type,
            'destination': '/opt/nova/environments/%s' % stack.stack_type
        }, {
            'source': 'env-vars/%s/docker-vars.list' % stack.stack_type,
            'destination': '/opt/nova/environments/%s' % stack.stack_type
        }, {
            'source': 'env-vars/%s/docker-args.list' % stack.stack_type,
            'destination': '/opt/nova/environments/%s' % stack.stack_type
        }]

    def __generate_scripts(self, docker_image):
        deploy_scripts_path = os.path.join(templates.__path__[0], 'deploy-scripts')
        for f in os.listdir(deploy_scripts_path):
            file_name = os.path.join(deploy_scripts_path, f)
            shutil.copy(file_name, self._nova_deploy_dir)

        print(colored("Including default common scripts", color='cyan'))

        load_data = {
            'image': docker_image.get("RepoTags")[0],
            'image_filename': '%s-%s-docker-image.tar.gz' % (self._service_manager.service_name, self._build_id)
        }
        self.__render_script('load_docker_container.sh', LOAD_DOCKER_CONTAINER, load_data)
        print(colored("Load docker image script written.", color='green'))

        start_data = {
            'service_name': self._service_manager.service_name,
            'port': self._service_manager.service_port,
            'stack_type': self._stack.stack_type,
            'stack_name': self._stack.name,
            'environment_name': self._service_manager.environment.name,
            'image': docker_image.get("RepoTags")[0]
        }
        self.__render_script('start_docker_container.sh', START_DOCKER_CONTAINER, start_data)
        print(colored("Start docker container script written.", color='green'))

        validate_data = {
            'port': self._service_manager.service_port,
            'healthcheck_url': self._service_manager.service_healthcheck_url
        }
        self.__render_script('validate_service.sh', VALIDATE, validate_data)
        print(colored("Validate service script written.", color='green'))

    def __render_script(self, script_filename, template, data):
        script_template = Template(template, trim_blocks=True)
        script_body = str(script_template.render(data)).strip()
        self.__render_file(script_filename, script_body)

    def __render_file(self, filename, file_body):
        with open(os.path.join(self._nova_deploy_dir, filename), 'w') as f:
            f.write(file_body)
            f.write(os.linesep)

    def __cleanup(self):
        try:
            if os.path.exists(self._nova_deploy_dir):
                print(colored("Cleaning up deployment bundle...", color='green'))
                shutil.rmtree(self._nova_deploy_dir)
        except Exception as e:
            raise NovaError(e)
