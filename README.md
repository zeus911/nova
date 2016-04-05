NOVA
================

The NOVA cli application is a thin wrapper around the Amazon Web Services API to make creating infrastructure via CloudFormation and deploying Dockerized applications via CodeDeploy, even easier and faster.

![](http://i.imgur.com/1g6RV2E.gif)

# Getting Started


## Requirements & Assumptions

- Python 2.7
- [AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html) is already setup.
- Docker is installed and running locally.

## Installing NOVA

Install or upgrade to the latest version of NOVA with pip:

    pip install -U gilt-nova

## Service Descriptor

To start using, you need to write your `nova.yml` file at the root of your application directory. Your NOVA descriptor file, describes your service and its environments, so the NOVA tool knows how to create its infrastructure and deploy it to said infrastructure.

The schema for the `nova.yml` file is [here](nova/core/spec/nova_service_schema.yml).

Your `nova.yml` file describes the infrastructure needed to run your service. An environment is a group of stacks to be deployed to an AWS account, most services will only have one environment. You can use multiple environments for deploying applications across AWS accounts and/or regions. An environment has multiple stacks, these are for example production, live-canary and dark-canary/staging stacks.

Once you've written your `nova.yml` file, all you need to do is run `nova stack create <environment name>`. Once Cloudformation has finished creating all your environments' resources, you can run `nova deploy <environment name> <stack name>`. If you already have an existing service running in production, you can now move traffic to your new instances and remove the old infrastructure.

Usage Steps:

1. Write `nova.yml` service descriptor.
2. `nova stack create <environment name>`
3. `nova deploy <environment name> <stack name>`


# Documentation

__NOTICE: Documentation is still a work in progress.__

# Common Install Issues

See [Troubleshooting Install](TROUBLESHOOTING_INSTALL.md)


# Development

To begin developing the virtual environment needs to be activated:

    mkvirtualenv nova
    workon nova
    python setup.py develop
    
## Releasing

One-time Install zest.releaser

    pip install zest.releaser[recommended]

To release:

    fullrelease

When you're finished:

    deactivate
