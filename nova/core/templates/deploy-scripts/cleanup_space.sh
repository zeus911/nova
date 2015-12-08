#!/usr/bin/env bash

# Cleanup last deployment from tmp
rm -f /tmp/*-docker-image.tar.gz

# Clear down code-deploy previous deployments except last successful install

DEPLOY_INSTRUCTIONS=/opt/codedeploy-agent/deployment-root/deployment-instructions/
DEPLOY_ROOT=/opt/codedeploy-agent/deployment-root/

for d in ${DEPLOY_ROOT}*; do
[[ -d $d && "${d##*/}" != "deployment-instructions" ]] || continue
    for f in $d/*; do
    [[ -e $f && "$f" != $(cat ${DEPLOY_INSTRUCTIONS}${d##*/}_last_successful_install) ]] || continue
    if [[ $f == ${DEPLOY_ROOT}* ]]
    then
      $(rm -rf $f)
    fi
    done
done
