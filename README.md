NOVA
================

**Collection of utilities to easily deploy services to AWS.**


![](http://i.imgur.com/1g6RV2E.gif)

# Gimme gimme gimme

Install or upgrade to the latest version of Nova with PIP:

    pip install -U gilt-nova

To start using, you need to write your `nova.yml` file.

Your `nova.yml` file describes the infrastructure needed to run your service. The descriptor file is split into __environments__ and __stacks__. An environment is a group of stacks to be deployed to an AWS account, most services will only have one environment (the only services to have two are those that stand up a sandbox environment in backoffice). An environment has multiple stacks, these are for example production, live-canary and dark-canary/staging stacks.

Once you've written your `nova.yml` file, all you need to do is run `nova stack create <stack name>`. Once Cloudformation has finished creating all your environments' resources, you can run `nova deploy <environment name> <stack name>`. If you already have an existing service running in production, you can now move traffic to your new instances and remove the old infrastructure.

Usage Steps:

1. Write `nova.yml` service descriptor.
2. `nova stack create <stack name>`
3. `nova deploy <environment name> <stack name>`


# Documentation

__NOTICE: Documentation is still a work in progress.__

See the [Wiki](https://github.com/gilt/nova/wiki)

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
