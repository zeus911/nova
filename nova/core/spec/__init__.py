from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import yaml


def resource_name(snake_case):
    return snake_case.title().replace('-', '').replace('_', '')


def yaml_include(loader, node):
    with open(node.value) as inputfile:
        return yaml.load(inputfile)
