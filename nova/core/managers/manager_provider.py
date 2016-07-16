from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from nova.core.managers.aws_manager import AwsManager
from nova.core.managers.docker_manager import DockerManager
from nova.core.managers.version_manager import VersionManager


class ManagerProvider(object):

    def __init__(self):
        pass

    @staticmethod
    def aws_manager(profile, region):
        return AwsManager(profile, region)

    @staticmethod
    def docker_manager():
        return DockerManager()

    @staticmethod
    def version_manager():
        return VersionManager()
