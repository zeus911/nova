===================
**Getting Started**
===================

This page describes how to download, install and use the basic functionality of gilt-nova.

**Installation**
################

To install gilt-nova:

**Mac OS X**
============

In practice, it's common to run into python environment issues, so I've included steps to setup that too.
- Install pyenv, pyenv-virtualenv pyenv-virtualenvwrapper & gilt-nova

::

    brew install pyenv pyenv-virtualenv pyenv-virtualenvwrapper
    echo 'if which pyenv > /dev/null; then eval "$(pyenv init -)"; fi' >> ~/.zshrc
    echo 'if which pyenv-virtualenv-init > /dev/null; then eval "$(pyenv virtualenv-init -)"; fi' >> ~/.zshrc
    source ~/.zshrc
    pyenv install 3.5.1
    pyenv global 3.5.1
    pyenv virtualenvwrapper
    pip install gilt-nova

If you want to use shared templates (recommended), you'll need to create the ``~/.nova`` directory. It's recommended that you
create this as a source controlled repository, that way changes are tracked.
- Create shared templates directory.

::

    git clone git@github.com:<username>/<template repository>.git ~/.nova


**Prerequisites**
#################

- Your service is bundled as a Docker image and uses Git as version control.
- You have the `AWS CLI <http://docs.aws.amazon.com/cli/latest/userguide/installing.html>`_ installed and configured.
- Your AWS accounts must have an `account alias <http://docs.aws.amazon.com/IAM/latest/UserGuide/console_account-alias.html>`_ setup in IAM.
- Your service's Docker image must end with the format ``<service name>:<version>``, NOVA searches your local Docker images for this to export.
- CodeDeploy in your AWS account must have the deployment configurations you specify in ``nova.yml`` already setup.


**Instance Prerequisites**
##########################

Your EC2 instances must at a minimum have the following:

- Installed packages:
    - Docker
    - Python
    - CloudWatch Logs Agent (NOVA will configure it)
    - CodeDeploy agent
    - gilt-nova

- Your instance has the NOVA Tool instance-scripts deployed locally to ``/opt/nova``. Run the following on your instance.

::

    sudo nova setup
