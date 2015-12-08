import yaml


def resource_name(snake_case):
    return snake_case.title().replace('-', '').replace('_', '')


def yaml_include(loader, node):
    with file(node.value) as inputfile:
        return yaml.load(inputfile)
