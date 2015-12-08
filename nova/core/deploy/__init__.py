

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

IFS=$'\r\n' GLOBIGNORE='*' command eval  'docker_args=($(cat /opt/nova/environments/{{stack_type}}/docker-vars.list))'

eval docker run -d \
  --name={{service_name}} \
  -p {{port}}:{{port}} \
  $(< /opt/nova/environments/{{stack_type}}/docker-opts.list) \
  ${docker_args[@]} \
  $(< /opt/nova/environments/{{stack_type}}/docker-vols.list) \
  {{image}} \
  $(< /opt/nova/environments/{{stack_type}}/docker-args.list)
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
