from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import subprocess
from termcolor import colored
from docker import Client as DockerClient
from docker.utils import kwargs_from_env

from nova.core import NovaError


class DockerManager(object):

    def __init__(self):
        self._docker_client = None

    @property
    def docker_client(self):
        if self._docker_client is None:
            kwargs = kwargs_from_env()
            try:
                kwargs['tls'].assert_hostname = False
            except KeyError:
                pass
            kwargs['version'] = 'auto'
            self._docker_client = DockerClient(**kwargs)
        return self._docker_client

    def images(self):
        return self.docker_client.images()

    def find_image(self, looking_for_tag):
        matching_images = [d for d in self.images() if d["RepoTags"][0].endswith(looking_for_tag)]
        if not len(matching_images) == 1:
            raise NovaError("Could not find a docker image with a tag for: '%s'" % looking_for_tag)
        else:
            return matching_images[0]

    def save_docker_image_with_tag(self, looking_for_tag, out_file):
        docker_image = self.find_image(looking_for_tag)
        print(colored("Found docker image '%s'." % docker_image.get("RepoTags")[0], color='green'))
        print(colored("Exporting docker image to include in bundle...", color='cyan'))
        save_cmd = ['docker', 'save', '-o', out_file, docker_image.get("RepoTags")[0]]
        p = subprocess.Popen(save_cmd, stdout=subprocess.PIPE)
        while p.poll() is None:
            print(colored(p.stdout.readline(), color='magenta'))
        print(colored(p.stdout.read(), color='magenta'))
        return docker_image
