#!/bin/bash


export LC_ALL="en_US.UTF-8"
export LANG="en_US.UTF-8"

# apt defaults
export DEBIAN_FRONTEND=noninteractive

STACK_NAME=$1
STACK_TYPE=$2
WAIT_HANDLE_REF=$4

EC2_AVAIL_ZONE=$( curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone )
EC2_REGION="`echo \"$EC2_AVAIL_ZONE\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"

# Upgrade to latest Amazon AMI
yum update -y

# Upgrade to latest nova tool
pip install -U gilt-nova

# Fix unknown host issue
echo "$(curl http://169.254.169.254/latest/meta-data/local-ipv4) $(curl http://169.254.169.254/latest/meta-data/local-hostname|cut -d . -f1) $(curl http://169.254.169.254/latest/meta-data/local-hostname|cut -d . -f1).ec2.internal" >> /etc/hosts


echo "Clearing old logs..."

find . -type f -name 'application.lo*' -exec sh -c '
  for f do
    echo -n > $f
  done' sh {} +

echo -n > /var/log/syslog


echo "INFO: Notifying CloudFormation (region: $EC2_REGION, stack: $STACK_NAME, resource: $WAIT_HANDLE_REF)..."

[ -z "$WAIT_HANDLE_REF" ] || cfn-signal -e 0 --stack $STACK_NAME --region $EC2_REGION "$WAIT_HANDLE_REF"
