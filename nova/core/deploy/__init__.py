

LOAD_DOCKER_CONTAINER="""
#!/usr/bin/env bash

set -e

if [[ "$(docker images -q {{image}} 2> /dev/null)" == "" ]]; then
    exec docker load -i /tmp/{{image_filename}}
fi
"""

START_DOCKER_CONTAINER="""
#!/usr/bin/env bash

set -e

INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
REGION=$(curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | grep region | awk -F\\" '{print $4}')

STACK_ENV=`aws ec2 describe-tags --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=Environment" --region=$REGION --output=text | awk '{print $5}'`

IFS=$'\r\n' GLOBIGNORE='*' command eval  'docker_args=($(cat /opt/nova/environments/$STACK_ENV/docker-vars.list))'

eval docker run -d \
  --name={{service_name}} \
  -p {{port}}:{{port}} \
  $(< /opt/nova/environments/$STACK_ENV/docker-opts.list) \
  ${docker_args[@]} \
  $(< /opt/nova/environments/$STACK_ENV/docker-vols.list) \
  {{image}} \
  $(< /opt/nova/environments/$STACK_ENV/docker-args.list)
"""

VALIDATE="""
#!/bin/bash

set -x

n=0
until [ $n -ge 30 ]
do
    sleep 10;
    res=`curl -s -I localhost:{{port}}{{healthcheck_url}} | grep HTTP/1.1 | awk {'print $2'}`
    echo $res;

    if [ $res -eq 200 ]
     then
      exit 0;
    fi
    n=$[$n+1]
done

exit 1;
"""
