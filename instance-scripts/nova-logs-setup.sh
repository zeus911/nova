#!/bin/bash

export LC_ALL="en_US.UTF-8"
export LANG="en_US.UTF-8"

# apt defaults
export DEBIAN_FRONTEND=noninteractive

APP_NAME=$1
LOGS_LIST=$2

mkdir -pv /var/log/${APP_NAME}
chmod a+w /var/log/${APP_NAME}

python /opt/nova/configure-cloudwatch-logs-agent.py "$LOGS_LIST"

service awslogs restart