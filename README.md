[![Build Status](https://travis-ci.org/gilt/nova.svg?branch=master)](https://travis-ci.org/gilt/nova) [![Coverage](https://coveralls.io/repos/github/gilt/nova/badge.svg?branch=master)](https://coveralls.io/github/gilt/nova?branch=master) [![license](https://img.shields.io/github/license/gilt/nova.svg)](https://github.com/gilt/nova/blob/master/LICENSE) [![latest](https://img.shields.io/pypi/v/gilt-nova.svg)](https://pypi.python.org/pypi/gilt-nova/)  [![python](https://img.shields.io/pypi/pyversions/gilt-nova.svg)](https://pypi.python.org/pypi/gilt-nova/)
[![Documentation Status](https://readthedocs.org/projects/gilt-nova/badge/?version=latest)](http://gilt-nova.readthedocs.io/en/latest/?badge=latest)
[![Gitter](https://badges.gitter.im/gilt/nova.svg)](https://gitter.im/gilt/nova)

NOVA
================

The NOVA cli application is a thin wrapper around the Amazon Web Services API to make creating infrastructure via CloudFormation and deploying Dockerized applications via CodeDeploy, even easier and faster.

![](http://i.imgur.com/1g6RV2E.gif)

# Getting Started

## Requirements & Assumptions

- Python 2.7+
- [AWS Command Line Interface](http://docs.aws.amazon.com/cli/latest/userguide/installing.html) is already setup.
- Docker is installed and running locally.

## Installing NOVA

Install or upgrade to the latest version of NOVA with pip:

    pip install -U gilt-nova


# Documentation

See [Read The Docs](http://gilt-nova.readthedocs.io/en/latest/)


# Common Issues

See [Troubleshooting](TROUBLESHOOTING.md)


# Development

To begin developing the virtual environment needs to be activated:
    
    pyenv virtualenv 3.5.1 nova
    pyenv activate nova
	pip install -r requirements.txt
    python setup.py develop

## Pre-Release

    python setup.py sdist upload -r pypitest
    pip install -U --pre -i https://testpypi.python.org/pypi gilt-nova

## Releasing

One-time Install zest.releaser

    pip install zest.releaser[recommended]

To release:

    fullrelease

When you're finished:

    deactivate
